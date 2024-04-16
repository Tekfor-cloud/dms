import base64
import logging
import uuid
import io

from collections import defaultdict
from odoo import models, fields, api, tools

from botocore.exceptions import ClientError

from ..utils.connection import Connection, get_bucket_name

_logger = logging.getLogger(__name__)


class File(models.Model):
    _inherit = "dms.file"

    s3_object = fields.Char(readonly=True)

    def _compute_content(self):
        bin_recs = self.with_context({"bin_size": True})
        records = bin_recs.filtered(lambda rec: rec.storage_id.save_type == "s3")
        if records:
            conn = Connection()

            for rec in records.with_context(self.env.context):
                if rec.s3_object:
                    try:
                        bucket_name = get_bucket_name(rec.storage_id.name)
                        with io.BytesIO() as descriptor:
                            conn.download_fileobj(
                                bucket_name, rec.s3_object, descriptor
                            )
                            descriptor.seek(0)
                            rec.content = base64.b64encode(descriptor.read())

                    except Exception:
                        _logger.exception("S3 exception")
                        _logger.info(
                            "File '%s' missing on S3 object storage", rec.s3_object
                        )

                        rec.content = False
                else:
                    rec.content = False
        return super(File, self - records)._compute_content()

    def _inverse_content(self):
        records = self.filtered(lambda rec: rec.storage_id.save_type == "s3")
        if records:
            updates = defaultdict(set)
            conn = Connection()
            for rec in records:
                values = self._get_content_inital_vals()
                binary = base64.b64decode(rec.content or "")
                values = rec._update_content_vals(values, binary)
                updates[tools.frozendict(values)].add(rec.id)

                key = rec.s3_object or values["s3_object"]
                bucket_name = get_bucket_name(rec.storage_id.name)
                conn.upload_fileobj(io.BytesIO(binary), bucket_name, key)

            with self.env.norecompute():
                for vals, ids in updates.items():
                    self.browse(ids).write(dict(vals))
        return super(File, self - records)._inverse_content()

    def _compute_save_type(self):
        bin_recs = self.with_context({"bin_size": True})
        records = bin_recs.filtered(lambda rec: rec.storage_id.save_type == "s3")
        for record in records.with_context(self.env.context):
            record.save_type = "s3"
        return super(File, self - records)._compute_save_type()

    @api.model
    def _update_content_vals(self, vals, binary):
        vals = super(File, self)._update_content_vals(vals, binary)
        if not self.s3_object:
            vals.update({"s3_object": str(uuid.uuid4())})
        return vals

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        if not default:
            default = {}

        if default.get("s3_object", self.s3_object) == self.s3_object:
            default["s3_object"] = False

        default["content"] = self.content

        return super().copy(default)

    def unlink(self):
        to_delete_in_s3 = defaultdict(set)
        for rec in self:
            if rec.storage_id.save_type == "s3" and rec.s3_object:
                to_delete_in_s3[get_bucket_name(rec.storage_id.name)].add(rec.s3_object)

        res = super().unlink()

        if to_delete_in_s3:
            conn = Connection()
        for bucket_name, object_list in to_delete_in_s3.items():
            try:
                conn.delete_objects(bucket_name, object_list)
            except ClientError:
                _logger.exception("Exception in object deletion from s3")
        return res
