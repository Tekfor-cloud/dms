import base64
import logging
import uuid
import io

from collections import defaultdict
from odoo import models, fields, api, tools

from swiftclient.exceptions import ClientException

from ..utils.connection import get_swift_connection


class File(models.Model):
    _inherit = "dms.file"

    swift_object = fields.Char(readonly=True)

    def _compute_content(self):
        bin_recs = self.with_context({"bin_size": True})
        records = bin_recs.filtered(lambda rec: rec.storage_id.save_type == "swift")
        if records:
            conn = get_swift_connection()
            for rec in records.with_context(self.env.context):
                if rec.swift_object:
                    rec.content = base64.b64encode(
                        conn.get_object(rec.storage_id.name, rec.swift_object)[1]
                    )
                else:
                    rec.content = False
        return super(File, self - records)._compute_content()

    @api.multi
    def _inverse_content(self):
        records = self.filtered(lambda rec: rec.storage_id.save_type == "swift")
        if records:
            updates = defaultdict(set)
            conn = get_swift_connection()
            for rec in records:
                values = self._get_content_inital_vals()
                binary = base64.b64decode(rec.content or "")
                values = rec._update_content_vals(values, binary)
                updates[tools.frozendict(values)].add(rec.id)

                conn.put_object(
                    rec.storage_id.name,
                    rec.swift_object or values["swift_object"],
                    io.BytesIO(binary),
                )

            with self.env.norecompute():
                for vals, ids in updates.items():
                    self.browse(ids).write(dict(vals))
        return super(File, self - records)._inverse_content()

    def _compute_save_type(self):
        bin_recs = self.with_context({"bin_size": True})
        records = bin_recs.filtered(lambda rec: rec.storage_id.save_type == "swift")
        for record in records.with_context(self.env.context):
            record.save_type = "swift"
        return super(File, self - records)._compute_save_type()

    @api.model
    def _update_content_vals(self, vals, binary):
        vals = super(File, self)._update_content_vals(vals, binary)
        if not self.swift_object:
            vals.update({"swift_object": str(uuid.uuid4())})
        return vals

    @api.multi
    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        if not default:
            default = {}

        if default.get("swift_object", self.swift_object) == self.swift_object:
            default["swift_object"] = False

        default["content"] = self.content

        return super().copy(default)

    @api.multi
    def unlink(self):
        to_delete_in_swift = []
        for rec in self:
            if rec.storage_id.save_type == "swift" and rec.swift_object:
                to_delete_in_swift.append(
                    {
                        "container": rec.storage_id.name,
                        "object": rec.swift_object,
                    }
                )

        res = super().unlink()

        if to_delete_in_swift:
            conn = get_swift_connection()
        for swift_object in to_delete_in_swift:
            try:
                conn.delete_object(
                    swift_object["container"],
                    swift_object["object"],
                )
            except ClientException as exp:
                if exp.http_status == 404:
                    logging.warning(
                        "Object %s was not found in swift object storage",
                        swift_object["object"],
                    )
                else:
                    raise
        return res
