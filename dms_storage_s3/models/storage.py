from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError

from ..utils.connection import Connection, BucketAlreadyExistsException, get_bucket_name


class Storage(models.Model):
    _inherit = "dms.storage"

    save_type = fields.Selection(
        selection_add=[("s3", "S3")],
        ondelete={"s3": "set default"},
    )

    s3_recovery_directory_id = fields.Many2one(
        "dms.directory", domain="[('storage_id', '=', active_id)]"
    )

    @api.model
    def create(self, values):
        rec = super(Storage, self).create(values)
        if rec.save_type == "s3":
            conn = Connection()
            conn.create_bucket(get_bucket_name(values["name"]))
        return rec

    def write(self, values):
        res = super(Storage, self).write(values)
        if values.get("save_type") == "s3":
            conn = Connection()
            for rec in self:
                try:
                    conn.create_bucket(get_bucket_name(rec.name))
                except BucketAlreadyExistsException:
                    raise ValidationError(
                        _("Bucket {} already exists").format(rec.name)
                    )

        if values.get("name"):
            for rec in self.filtered(lambda r: r.save_type == "s3"):
                raise ValidationError(_("A s3 storage can't be rename"))

        return res

    def unlink(self):
        """Allow to delete a storage only if associated with an empty bucket.
        If this is the case, the bucket is deleted along with storage"""
        conn = Connection()
        try:

            conn.delete_bucket()
        except Exception:
            pass

        raise UserError("TO BE IMPLEMENTED")
