/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { FormCompiler } from "@web/views/form/form_compiler";
import { append, createElement, setAttributes } from "@web/core/utils/xml";

patch(FormCompiler.prototype, {
    compile(node, params) {
        const res = super.compile(node, params);

        const chatterContainerHookXml = res.querySelector(".o-mail-Form-chatter:not(.o-isInFormSheetBg)");

        if (!chatterContainerHookXml) {
            return res;
        }

        if (odoo.web_chatter_position === "bottom") {
            const formSheetBgXml = res.querySelector(".o_form_sheet_bg");
            const chatterExists = formSheetBgXml.querySelector(".o-mail-Form-chatter.o-isInFormSheetBg");
            if (chatterExists) {
                return res;
            }

            const sheetBgChatterContainerHookXml = chatterContainerHookXml.cloneNode(true);
            setAttributes(sheetBgChatterContainerHookXml, {
                "t-if": "true",
                "t-attf-class": `"mt-4 mt-md-0"`,
            });
            append(formSheetBgXml, sheetBgChatterContainerHookXml);
            const sheetBgChatterContainerXml = sheetBgChatterContainerHookXml.querySelector(
                "t[t-component='__comp__.mailComponents.Chatter']"
            );
            setAttributes(sheetBgChatterContainerXml, {
                isInFormSheetBg: "true",
                isChatterAside: "false",
            });

            setAttributes(chatterContainerHookXml, {
                "t-if": false,
            });
        }

        if (odoo.web_chatter_position === "manual") {
            setAttributes(chatterContainerHookXml, {
                "t-att-class": "{'hidden': __comp__.chatterPreviewState.chatterHidden,'hide_chatter_control': true}",
                "t-ref": "chatterContainer",
            });

            const chatterContainerControlHookXml = createElement("div");
            chatterContainerControlHookXml.classList.add("o_chatter_control");
            setAttributes(chatterContainerControlHookXml, {
                "t-on-click": "__comp__.togglePreview.bind(__comp__)",
            });
            append(chatterContainerHookXml, chatterContainerControlHookXml);

            const chatterContainerResizeHookXml = createElement("span");
            chatterContainerResizeHookXml.classList.add("o_resize");
            setAttributes(chatterContainerResizeHookXml, {
                "t-on-click.stop.prevent": "",
                "t-on-mousedown.stop.prevent": "__comp__.onStartResize.bind(__comp__)",
            });
            append(chatterContainerHookXml, chatterContainerResizeHookXml);
        }

        return res;
    }
});


