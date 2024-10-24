odoo.define('muk_web_preview.binary_force_bin', function (require) {
    "use strict";

    /*
    NOTE :
    L'erreur se trouve au "data: utils.is_bin_size(this.value) ? null : this.value,"
    Normalement (si on choisit le stockage database) la valeur de this.value est "XXX Kb" (taille du fichier)
    Hors ici le fichier est renvoyé entierement en base64
    J'ai donc forcé le widget a ne pas renvoyé le data ce qui pousse odoo a bien renvoyer le fichier

    PISTE:
    def _compute_content(self)
    Les autres stockages du muk_dms montre l'ajout du context {"base64": True} hors il n'est pas spécifié dans le code du localfs
    */

    var core = require('web.core');
    var utils = require('web.utils');
    var session = require('web.session');
    var fields = require('web.basic_fields');
    var registry = require('web.field_registry');
    var field_utils = require('web.field_utils');

    var PreviewManager = require('muk_preview.PreviewManager');
    var PreviewDialog = require('muk_preview.PreviewDialog');

    var _t = core._t;
    var QWeb = core.qweb;

    fields.FieldBinaryFile.include({
        _onPreviewButtonClick: function (event) {
            var filename_fieldname = this.attrs.filename;
            var last_update = this.recordData.__last_update;
            var mimetype = this.recordData['mimetype'] || null;
            var filename = this.recordData[filename_fieldname] || null;
            var unique = last_update && field_utils.format.datetime(last_update);
            console.log(this.recordData);
            var binary_url = session.url('/web/content', {
                model: this.model,
                id: JSON.stringify(this.res_id),
                // data: utils.is_bin_size(this.value) ? null : this.value,
                data: null,
                unique: unique ? unique.replace(/[^0-9]/g, '') : null,
                filename_field: filename_fieldname,
                filename: filename,
                field: this.name,
                download: true,
            });
            var preview = new PreviewDialog(
                this, [{
                    url: binary_url,
                    filename: filename,
                    mimetype: mimetype,
                }], 0
            );
            preview.appendTo($('body'));
            event.stopPropagation();
            event.preventDefault();
        },
    });

    var FieldBinaryPreview = fields.FieldBinaryFile.extend({
        template: 'muk_preview.FieldBinaryPreview',
        _renderReadonly: function () {
            this._renderPreview();
        },
        _renderEdit: function () {
            if (this.value) {
                this.$('.mk_field_preview_container').removeClass("o_hidden");
                this.$('.o_select_file_button').first().addClass("o_hidden");
                this._renderPreview();
            } else {
                this.$('.mk_field_preview_container').addClass("o_hidden");
                this.$('.o_select_file_button').first().removeClass("o_hidden");
            }
        },
        _renderPreview: function () {
            this.$('.mk_field_preview_container').empty();
            var filename_fieldname = this.attrs.filename;
            var last_update = this.recordData.__last_update;
            var filename = this.recordData[filename_fieldname] || null;
            var unique = last_update && field_utils.format.datetime(last_update);
            var binary_url = session.url('/web/content', {
                model: this.model,
                id: JSON.stringify(this.res_id),
                // data: utils.is_bin_size(this.value) ? null : this.value,
                data: null,
                unique: unique ? unique.replace(/[^0-9]/g, '') : null,
                filename_field: filename_fieldname,
                filename: filename,
                field: this.name,
                download: true,
            });
            var manager = new PreviewManager(
                this, [{
                    url: binary_url,
                    filename: filename,
                    mimetype: undefined,
                }], 0
            );
            manager.appendTo(this.$('.mk_field_preview_container'));
        },
        on_save_as: function (event) {
            event.stopPropagation();
        },
    });

    registry.add('binary_preview_force', FieldBinaryPreview);

    return FieldBinaryPreview;

});
