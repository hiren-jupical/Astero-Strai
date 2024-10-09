// odoo.define('strai.strai_drag_attachement', function (require) {
// "use strict";
//
// var Dialog = require('web.Dialog');
// var widgetRegistry = require('web.widget_registry');
// var Widget = require('web.Widget');
// var core = require("web.core");
// var qweb = core.qweb;
// var _t = core._t;
//
// var DragDropAttachements = Widget.extend({
//     // template: 'DragAttachmentWidget',
//     events: {
//         'dragover div.drag_attachment': '_add_drag_attachment_area',
//         'dragleave div.o_drag_area': '_attachmentDragOut',
//         'drop div.o_drag_area': '_on_drop_attachment',
//         'click .o_attachment_delete': '_onDelete',
//     },
//
//     init: function (parent, record, nodeInfo) {
//         this._super.apply(this, arguments);
//         if(!record.res_id){
//             this.res_id = record.data.res_id;
//             this.res_model = record.data.model
//             this.is_drag_attachment = true
//         }else{
//             this.res_id = record.res_id;
//             this.res_model = record.model;
//             this.is_drag_attachment = false
//         }
//         this.file_uploaded = []
//         this.dragCount = 0;
//     },
//
//     start: function () {
//         this.$el.html(qweb.render('DragAttachmentWidget', {widget: this}));
//         this._super.apply(this, arguments);
//     },
//
//     willStart: function () {
//         var self = this;
//         return this._super.apply(this, arguments).then(function () {
//             return self._rpc({
//                 model: 'ir.attachment',
//                 method: 'search_read',
//                 args: [[['is_drag_attachment', '=', true],
//                     ['res_id', '=', self.res_id],
//                     ['res_model', '=', self.res_model]], []],
//             }).then(function (attachment_ids) {
//                 for (let i in attachment_ids){
//                     self._rpc({
//                         model: 'ir.attachment',
//                         method: 'unlink',
//                         args: [attachment_ids[i]['id']],
//                     });
//                 }
//             });
//         });
//     },
//
//     _add_drag_attachment_area: function () {
//         if (this.dragCount === 0){
//             this._drag_attchment_area = $(
//                 qweb.render("strai.drag_drop_attachment", {id: this.res_id})
//             );
//             this.$el.append(this._drag_attchment_area);
//             this.$el.on("dragover", (ev) => {
//                 ev.preventDefault();
//                 if (_.isEmpty(ev.originalEvent.dataTransfer.files)){
//                     const drop_zone_offset = this.$el.offset();
//                     this._drag_attchment_area.css({
//                         top: (drop_zone_offset.top - 30),
//                         left: (drop_zone_offset.left - 30),
//                         width: 300,
//                         height: 300,
//                     });
//                     this._drag_attchment_area.removeClass("d-none");
//                 }
//                 if (!this.res_id){
//                     Dialog.alert(this, _t("Please save the record first before adding attachments."));
//                     this._drag_attchment_area.addClass("d-none");
//                 }
//             });
//             this.dragCount += 1
//         }
//         this._drag_attchment_area.on("dragleave", (ev) => {
//             this._attachmentDragOut()
//         });
//     },
//
//     _attachmentDragOut: function (ev) {
//         if (this.dragCount > 0){
//             this.dragCount -= 1;
//         }
//         if (this.dragCount === 0) {
//             this._drag_attchment_area.hide()
//         }
//     },
//
//     _on_drop_attachment: function (ev) {
//         if (this._drag_attchment_area) {
//             ev.preventDefault();
//             const attchment = (ev) => {
//                 var attchment_files = ev.originalEvent.dataTransfer.files
//                 for (let file of Object.values(attchment_files)) {
//                     const file_reader = new FileReader();
//                     file_reader.readAsDataURL(file);
//                     file_reader.onloadend = (file_reader) => {
//                         var datas = file_reader.target.result
//                         var data_to_replace = 'data:' + file.type + ';base64,';
//                         datas = datas.replace(data_to_replace, "")
//                         this._rpc({
//                             model: 'ir.attachment',
//                             method: 'create',
//                             args: [{
//                                 name: file.name,
//                                 datas: datas,
//                                 res_model: this.res_model,
//                                 res_id: this.res_id,
//                                 is_drag_attachment: this.is_drag_attachment,
//                                 is_sale_attachment: this.is_drag_attachment ? false : true,
//                             }]
//                         }).then((attachment) => {
//                             var attachment_info = {
//                                 'url': '/web/content/'+ attachment +'?download=true',
//                                 'file': file.name,
//                                 'attachment_id': attachment
//                             };
//                             this.file_uploaded.push(attachment_info)
//                             this.$('.drag_attachment_preview_main').replaceWith($(qweb.render('DragAttachmentPreview', {widget: this})));
//                             this._attachmentDragOut()
//                         });
//                     }
//                     file_reader.onerror = (error) => {
//                         console.log('Error: ', error);
//                     };
//                 }
//             }
//             attchment(ev)
//         }
//     },
//
//     _onDelete: function (ev) {
//         var attachment_id = $(ev.currentTarget).data('id');
//         if (attachment_id) {
//             this._rpc({
//                 model: 'ir.attachment',
//                 method: 'unlink',
//                 args: [attachment_id],
//             });
//             for (let i in this.file_uploaded){
//                 if (this.file_uploaded[i]['attachment_id'] == attachment_id){
//                     this.file_uploaded.splice(i, 1);
//                 }
//             }
//         }
//         this.$('.'+attachment_id).remove()
//     },
// });
// widgetRegistry.add('drag_drop_attachements', DragDropAttachements);
// });