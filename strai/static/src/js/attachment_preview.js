/** @odoo-module */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

import { Component, onWillStart, onWillUpdateProps } from "@odoo/owl";

class AttachmentPrevieWidget extends Component {
    setup() {
        this.orm = useService('orm');
        this.res_model = this.props.record.resModel;

        onWillStart(async () => {
            await this.fetchAttachments(this.props.record.resId);
        });

        onWillUpdateProps(async (nextProps) => {
            this._attachment_ids = []
            $('.drag_attachment_preview_area').empty();
            await this.fetchAttachments(nextProps.record.resId);
        });
    }

    async fetchAttachments (res_id) {
        this._attachment_ids = await this.orm.call("ir.attachment", "search_read", [], {
            fields: ["id", "res_model", "res_id", "is_sale_attachment", "name"],
            domain: [
            '&',
            ['res_model', '=', this.res_model],
            ['res_id', '=', res_id],
            ['is_sale_attachment', '=', true],
        ]   
        });
    }

    async _onDeletepreviewattachment (ev) {
        var attachment_id = $(ev.currentTarget).data('id');
        await this.orm.call("ir.attachment", "unlink", [attachment_id], {});
        $('.'+attachment_id).remove()
    }
}

AttachmentPrevieWidget.template = "FormDragAttachmentPreview";

AttachmentPrevieWidget.props = {
    ...standardWidgetProps,
    string: { type: String },
};

export const attachmentPrevieWidget = {
    component: AttachmentPrevieWidget,
    extractProps: ({ attrs }) => {
        const { string } = attrs;
        return {
            string,
        };
    },
};

registry.category("view_widgets").add("Drag_AttachmentPreview", attachmentPrevieWidget);
