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

    def _compute_save_type(self):
        for record in self:
            if record.swift_object:
                record.save_type = "swift"
            else:
                super()._compute_save_type()

    def _update_content_vals(self, vals, binary):
        new_vals = super()._update_content_vals(vals, binary)
        if self.storage_id.save_type == "swift":
            if not self.swift_object:
                new_vals.update({"swift_object": str(uuid.uuid4())})
        return new_vals

    def write(self, vals):
        self.ensure_one()
        if self.storage_id.save_type in "swift":
            binary = vals.pop("content_binary")
            conn = get_swift_connection()
            conn.put_object(
                self.storage_id.name,
                self.swift_object or vals["swift_object"],
                io.BytesIO(binary),
            )
        return super().write(vals)

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        if not default:
            default = {}

        if default.get("swift_object", self.swift_object) == self.swift_object:
            default["swift_object"] = False

        default["content"] = self.content

        return super().copy(default)

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
