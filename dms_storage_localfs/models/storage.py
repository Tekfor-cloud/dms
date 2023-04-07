# Copyright 2023 TEKFor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from os import listdir, path

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class Storage(models.Model):

    _inherit = "dms.storage"

    save_type = fields.Selection(
        selection_add=[
            (
                "localfs",
                "Stores files in a given directory on local filesystem",
            )
        ]
    )

    local_store_directory = fields.Char(
        string="Root directory",
        help="The root directory where files are stored",
    )

    @api.multi
    def resync_directory(self):
        dmsdir_model = self.env["dms.directory"]
        for rec in self:
            if rec.save_type == "localfs":
                if not path.exists(rec.local_store_directory):
                    raise ValidationError(
                        _("Base directory does not exist: %s"),
                        rec.local_store_directory,
                    )

                # List localfs directories
                lst_dir = [
                    dir_name
                    for dir_name in listdir(rec.local_store_directory)
                    if path.isdir(path.join(rec.local_store_directory, dir_name))
                ]

                # List dms directories
                results = dmsdir_model.search(
                    [
                        ("root_storage", "=", rec.id),
                        ("name", "in", lst_dir),
                        ("is_root_directory", "=", True),
                    ]
                )

                # Create missing directories
                lst_existing_dir = results.mapped("name")
                for dir_name in [
                    dir_name for dir_name in lst_dir if dir_name not in lst_existing_dir
                ]:
                    results = results | dmsdir_model.create(
                        {
                            "name": dir_name,
                            "is_root_directory": True,
                            "root_storage": rec.id,
                        }
                    )

                # Sync child directories
                results.resync_directory()
