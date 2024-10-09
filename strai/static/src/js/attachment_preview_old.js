// odoo.define('strai.attachment_preview', function (require) {
// "use strict";
//
// const widgetRegistry = require('web.widget_registry');
// const Widget = require('web.Widget');
// const core = require("web.core");
// const qweb = core.qweb;
// const _t = core._t;
//
// var DragDropAttachementsPreview = Widget.extend({
// 	template: 'FormDragAttachmentPreview',
// 	events: {'click .o_attachment_delete': '_onDelete'},
//
// 	init: function (parent, record, nodeInfo) {
// 		this._super.apply(this, arguments)
// 		this.res_model = record.model;
// 		this.res_id = record.res_id;
// 	},
//
// 	willStart: function () {
// 		var self = this;
//         return this._super.apply(this, arguments).then(function () {
// 			var attachments = self._rpc({
// 				model: 'ir.attachment',
// 				method: 'search_read',
// 				args: [[['res_model', '=', self.res_model], ['res_id', '=', self.res_id], ['is_sale_attachment', '=', true]]],
// 			}).then(function (attachment_ids){
// 				self.$el.html(qweb.render('FormDragAttachmentPreview', {widget: attachment_ids}));
// 			});
// 		});
// 	},
//
// 	_onDelete: function (ev) {
// 		var self = this;
//         var attachment_id = $(ev.currentTarget).data('id');
//         if (attachment_id) {
//             self._rpc({
//                 model: 'ir.attachment',
//                 method: 'unlink',
//                 args: [attachment_id],
//             }).then(function (){
//             	self.trigger_up('reload');
//             })
//         }
//     },
// });
//
// widgetRegistry.add('Drag_AttachmentPreview', DragDropAttachementsPreview)
// });