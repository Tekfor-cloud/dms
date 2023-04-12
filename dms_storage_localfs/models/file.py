# Copyright 2023 TEKFor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

from os import sep, path
import shutil

from collections import defaultdict
from odoo import models, api, tools, exceptions, _


class File(models.Model):
    _inherit = "dms.file"

    def _compute_content(self):
        bin_recs = self.with_context({"bin_size": True})
        records = bin_recs.filtered(lambda rec: rec.storage_id.save_type == "localfs")
        for record in records.with_context(self.env.context):
            full_path = "{}{}{}".format(
                record.directory_id.get_full_path(), sep, record.name
            )
            try:
                if path.exists(full_path):
                    with open(full_path, "rb") as file:
                        record.content = base64.b64encode(file.read())
                else:
                    record.content = False

            except (IOError, OSError):
                logging.warning("Reading file %s failed!", full_path, exc_info=True)
                raise exceptions.ValidationError(
                    _("Unable to read file: %s") % full_path
                )
        return super(File, self - records)._compute_content()

    def _compute_save_type(self):
        bin_recs = self.with_context({"bin_size": True})
        records = bin_recs.filtered(lambda rec: rec.storage_id.save_type == "localfs")
        for record in records.with_context(self.env.context):
            record.save_type = "localfs"
        return super(File, self - records)._compute_save_type()

    @api.multi
    def _inverse_content(self):
        records = self.filtered(lambda rec: rec.storage_id.save_type == "localfs")
        updates = defaultdict(set)
        for record in records:
            values = self._get_content_inital_vals()
            binary = base64.b64decode(record.content or "")
            values = record._update_content_vals(values, binary)
            updates[tools.frozendict(values)].add(record.id)
            try:
                full_path = "{}{}{}".format(
                    record.directory_id.get_full_path(), sep, record.name
                )
                with open(full_path, "wb") as file:
                    file.write(binary)
            except (IOError, OSError):
                logging.warning("Reading file %s failed!", full_path, exc_info=True)
                raise exceptions.ValidationError(
                    _("Unable to write to file: %s") % full_path
                )
        with self.env.norecompute():
            for vals, ids in updates.items():
                self.browse(ids).write(dict(vals))
        return super(File, self - records)._inverse_content()

    # ==================================================================================
    # Write Create
    # ==================================================================================

    def write(self, values):
        moved_files = {}
        if "directory_id" in values:
            for rec in self:
                moved_files[rec.id] = path.join(
                    rec.directory_id.get_full_path(), rec.name
                )

        res = super(File, self).write(values)

        if moved_files:
            for rec in self:
                src = moved_files[rec.id]
                dst = path.join(rec.directory_id.get_full_path(), rec.name)
                if not path.exists(dst):
                    shutil.move(src, dst)
        return res
