/** @odoo-module **/


import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { browser } from "@web/core/browser/browser";

patch(ListRenderer.prototype, {

    setup() {
        super.setup(...arguments);
        this.rpc = useService("rpc");
        this.saveColumnTimeoutId = null;
    },

    /**
     * @override
     */
    computeColumnWidthsFromContent() {
        const columnWidths = super.computeColumnWidthsFromContent(...arguments);
        const table = this.tableRef.el;
        const thElements = [...table.querySelectorAll("thead th:not(.o_list_actions_header)")];
        thElements.forEach((el, elIndex) => {
            const fieldName = $(el).data("name");

            var columnObject = this.state.columns.find(item => item.name === fieldName);
            if (columnObject && 'attrs' in columnObject && 'column_width' in columnObject.attrs) {
                var column_width = parseInt(columnObject.attrs.column_width, 10);
                columnWidths[elIndex] = column_width;
            }
        });
        return columnWidths;
    },

    /**
     * @override
     */
    onStartResize(ev) {
        super.onStartResize(...arguments);

        const resizeStoppingEvents = ["keydown", "pointerdown", "pointerup"];
        const $th = $(ev.target.closest("th"));
        if (!$th || !$th.is("th")) {
            return;
        }
        const saveWidth = (saveWidthEv) => {
            if (saveWidthEv.type === "mousedown" && saveWidthEv.which === 1) {
                return;
            }
            ev.preventDefault();
            ev.stopPropagation();

            if (this.saveColumnTimeoutId) {
                clearTimeout(this.saveColumnTimeoutId);
            }

            const fieldName = $th.length ? $th.data("name") : undefined;
            if (this.props.list.resModel && fieldName && browser.localStorage) {
                browser.localStorage.setItem(
                    "odoo.columnWidth." + this.props.list.resModel + "." + fieldName,
                    parseInt(($th[0].style.width || "0").replace("px", ""), 10) || 0
                );
            }
            for (const eventType of resizeStoppingEvents) {
                browser.removeEventListener(eventType, saveWidth);
            }
            document.activeElement.blur();

            this.saveColumnTimeoutId = setTimeout(this.saveColumnWidth.bind(this), 2000);
        };
        for (const eventType of resizeStoppingEvents) {
            browser.addEventListener(eventType, saveWidth);
        }
    },

    async saveColumnWidth () {
        var viewId = this.env.config.viewId
        var fields = {}
        const table = this.tableRef.el;
        // custom
        if (table === null) {
            return;
        }
        // end custom
        const thElements = [...table.querySelectorAll("thead th:not(.o_list_actions_header)")];
        thElements.forEach((el, elIndex) => {
            const fieldName = $(el).data("name");
            if (this.props.list.resModel && fieldName && browser.localStorage) {
                const storedWidth = browser.localStorage.getItem(
                    `odoo.columnWidth.${this.props.list.resModel}.${fieldName}`
                );
                if (storedWidth) {
                    fields[fieldName] = parseInt(storedWidth, 10);
                }
            }
        });

        var listField = "";
        for (var key in fields) {
          listField += key + ": " + fields[key] + ";";
        }

        var orgData = await this.rpc('/save/column_width',
            {
                view_id: viewId,
                field_name: listField,
            }
        );
    }
});
