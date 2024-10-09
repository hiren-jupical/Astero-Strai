/** @odoo-module */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

import { Component, onWillUpdateProps } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { renderToElement } from "@web/core/utils/render";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

class DragAttachmentWidget extends Component {
    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        if(!this.props.record.resId){
            this.res_id = this.props.record.data.res_ids ? JSON.parse(this.props.record.data.res_ids)[0] : false
            this.res_model = this.props.record.data.model
            this.is_drag_attachment = true
        }else{
            this.res_id = this.props.record.resId;
            this.res_model = this.props.record.resModel;
            this.is_drag_attachment = false
        }

        onWillUpdateProps(async (nextProps) => {
            this.file_uploaded = []
            // this.res_id = nextProps.record.resId;
        });

        this.file_uploaded = []
        this.dragCount = 0;
    }

    _add_drag_attachment_area(ev) {
        var $drag_area = $(ev.currentTarget)

        if (this.dragCount === 0){
            this._drag_attchment_area = $(
                renderToElement("strai.drag_drop_attachment", {id: this.res_id})
            );
            $drag_area.append(this._drag_attchment_area);
            $drag_area.on("dragover", (ev) => {
                ev.preventDefault();
                if (ev.originalEvent.dataTransfer.files) {
                    const drop_zone_offset = $drag_area.offset();
                    this._drag_attchment_area.css({
                        top: (drop_zone_offset.top - 30),
                        left: (drop_zone_offset.left - 30),
                        width: 300,
                        height: 300,
                    });
                    this._drag_attchment_area.removeClass("d-none");
                }
                if (['sale', 'done', 'cancel'].includes(this.props.record.data.state)) {
                    this.dialog.add(AlertDialog, {
                        body: _t("you can not add attachments after 'Confirm' or 'Cancel' the SO."),
                    });
                    this._drag_attchment_area.addClass("d-none");
                }
                if (!this.res_id){
                    this.dialog.add(AlertDialog, {
                        body: _t("Please save the record first before adding attachments."),
                    });
                    this._drag_attchment_area.addClass("d-none");
                }
            });
            this.dragCount += 1
        }
        this._drag_attchment_area.on("dragleave", (ev) => {
            ev.preventDefault();
            this._attachmentDragOut()
        });
    }

    _attachmentDragOut (ev) {
        if (this.dragCount > 0){
            this.dragCount -= 1;
        }
        if (this.dragCount === 0 && this._drag_attchment_area) {
            this._drag_attchment_area.hide();
        }
    }

    _on_drop_attachment (ev) {
        if (this._drag_attchment_area) {
            ev.preventDefault();
            const attchment = (ev) => {
                var attchment_files = ev.dataTransfer.files
                for (let file of Object.values(attchment_files)) {
                    const file_reader = new FileReader();
                    file_reader.readAsDataURL(file);
                    file_reader.onloadend = async (file_reader) => {
                        var datas = file_reader.target.result
                        var data_to_replace = 'data:' + file.type + ';base64,';
                        if (!file.type) {
                            data_to_replace = 'data:application/octet-stream;base64,';
                        }
                        datas = datas.replace(data_to_replace, "")
                        var att_data = {
                            name: file.name,
                            datas: datas,
                            res_model: this.res_model,
                            res_id: this.res_id,
                            is_drag_attachment: this.is_drag_attachment,
                            is_sale_attachment: this.is_drag_attachment ? false : true,
                        };
                        var attachment = await this.orm.create("ir.attachment", [att_data], {});
                        var attachment_info = {
                            'url': '/web/content/'+ attachment +'?download=true',
                            'file': file.name,
                            'attachment_id': attachment
                        };
                        this.file_uploaded.push(attachment_info)
                        $('.drag_attachment_preview_area').replaceWith($(renderToElement('DragAttachmentPreview', {widget: this})));
                        this._attachmentDragOut()
                        this.$o_attachment_delete = $('.o_uploaded_attachment_delete')
                        this.$o_attachment_delete.on("click", (ev) => {
                            var attachment_id = $(ev.currentTarget).data('id');
                            this._onDeleteUploadedAttachment(attachment_id)
                        });
                    }
                    file_reader.onerror = (error) => {
                        console.log('Error: ', error);
                    };
                }
            }
            attchment(ev)
        }
    }

    async _onDeleteUploadedAttachment (attachment_id) {
        if (attachment_id) {
            await this.orm.call("ir.attachment", "unlink", [attachment_id], {});
            for (let i in this.file_uploaded){
                if (this.file_uploaded[i]['attachment_id'] == attachment_id){
                    this.file_uploaded.splice(i, 1);
                }
            }
        }
        $('.'+attachment_id).remove()
    }
}

DragAttachmentWidget.template = "DragAttachmentWidget";
DragAttachmentWidget.props = {
    ...standardWidgetProps,
    string: { type: String },
};
export const dragAttachmentWidget = {
    component: DragAttachmentWidget,
    extractProps: ({ attrs }) => {
        const { string } = attrs;
        return {
            string,
        };
    },
};

registry.category("view_widgets").add("drag_drop_attachements", dragAttachmentWidget);
