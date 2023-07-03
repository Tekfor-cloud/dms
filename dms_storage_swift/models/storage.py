from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError

from ..utils.connection import get_swift_connection


class Storage(models.Model):
    _inherit = "dms.storage"

    save_type = fields.Selection(selection_add=[("swift", "Swift")])

    swift_recovery_directory_id = fields.Many2one(
        "dms.directory", domain="[('storage_id', '=', active_id)]"
    )

    def swift_recovery(self):
        self.ensure_one()

        if not self.swift_recovery_directory_id:
            raise UserError(
                _("{} must be defined").format(
                    self._fields["swift_recovery_directory_id"].string
                )
            )
        elif self.swift_recovery_directory_id.storage_id != self:
            raise UserError(
                _("{} must be a folder of current storage").format(
                    self._fields["swift_recovery_directory_id"].string
                )
            )

        self.with_delay()._swift_recovery()

    def _swift_recovery(self):
        swift_object_list = self.storage_file_ids.mapped("swift_object")
        conn = get_swift_connection()
        for swift_object in conn.get_container(self.name, full_listing=True)[1]:
            if swift_object["name"] not in swift_object_list:
                self.env["dms.file"].create(
                    {
                        "name": swift_object["name"],
                        "directory_id": self.swift_recovery_directory_id.id,
                        "swift_object": swift_object["name"],
                    }
                )

    @api.model
    def create(self, values):
        rec = super(Storage, self).create(values)
        if rec.save_type == "swift":
            conn = get_swift_connection()
            conn.put_container(values["name"])
        return rec

    def write(self, values):
        res = super(Storage, self).write(values)
        if values.get("save_type") == "swift":
            conn = get_swift_connection()
            for rec in self:
                conn.put_container(rec.name)

        if values.get("name"):
            for rec in self.filtered(lambda r: r.save_type == "swift"):
                raise ValidationError(_("A swift storage can't be rename"))

        return res
