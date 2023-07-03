# Copyright 2023 TEKFor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from os import listdir, path, makedirs
import shutil


from odoo import models, api, _
from odoo.exceptions import ValidationError


class Directory(models.Model):

    _inherit = "dms.directory"

    def resync_directory(self):
        """
        Resync the directory content with local file system (localfs to dms.directory)
        """
        for rec in self:
            if rec.storage_id.save_type == "localfs":

                base_path = rec.storage_id.local_store_directory
                if not path.exists(base_path):
                    raise ValidationError(
                        _("Base directory does not exist: %s") % (base_path)
                    )

                full_path = rec.get_full_path()
                if not path.exists(full_path):
                    raise ValidationError(
                        _("Directory does not exist: %s") % (full_path)
                    )

                # List localfs directories
                lst_dir = [
                    dir_name
                    for dir_name in listdir(full_path)
                    if path.isdir(path.join(full_path, dir_name))
                ]

                # List dms directories
                results = self.search(
                    [
                        ("storage_id", "=", rec.storage_id.id),
                        ("name", "in", lst_dir),
                        ("is_root_directory", "=", False),
                        ("parent_id", "=", rec.id),
                    ]
                )

                # Create missing directories
                lst_existing_dir = results.mapped("name")
                for dir_name in [
                    dir_name for dir_name in lst_dir if dir_name not in lst_existing_dir
                ]:
                    results = results | self.create(
                        {
                            "name": dir_name,
                            "company": rec.company[0].id,
                            "is_root_directory": False,
                            "parent_id": rec.id,
                        }
                    )

                # Sync child directories
                results.resync_directory()

    def get_full_path(self):
        self.ensure_one()
        if self.is_root_directory:
            if self.storage_id.save_type == "localfs":
                return path.join(self.storage_id.local_store_directory, self.name)
            else:
                return self.name
        else:
            return path.join(self.parent_id.get_full_path(), self.name)

    def check_and_create_fs_directory(self, fpath):
        if not path.exists(fpath):
            makedirs(fpath)

    def write(self, values):
        """Create localfs directory if needed"""
        saved_full_path = {}
        for rec in self:
            saved_full_path[rec.id] = rec.get_full_path()

        res = super().write(values)

        for rec in self:
            if rec.storage_id.save_type == "localfs":
                src = saved_full_path[rec.id]
                dst = rec.get_full_path()
                if src != dst and not path.exists(dst):
                    shutil.move(src, dst)

        return res

    @api.model
    def create(self, values):
        """Create localfs directory"""
        rec = super().create(values)
        if rec.storage_id.save_type == "localfs":
            if values.get("parent_id"):
                parent_dir = self.env["dms.directory"].browse(values["parent_id"])
                self.check_and_create_fs_directory(
                    path.join(parent_dir.get_full_path(), rec.name)
                )
            elif values.get("root_storage_id"):
                root_stg = self.env["dms.storage"].browse(values["root_storage_id"])
                self.check_and_create_fs_directory(
                    path.join(root_stg.local_store_directory, rec.name)
                )

        return rec
