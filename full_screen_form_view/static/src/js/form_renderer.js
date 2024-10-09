/** @odoo-module **/


const { onMounted } = owl;
import { browser } from "@web/core/browser/browser";

import { patch } from "@web/core/utils/patch";
import { FormRenderer } from "@web/views/form/form_renderer";
patch(FormRenderer.prototype, {
    setup() {
        super.setup();
        if (browser.localStorage.getItem("full_screen") === 'true') {
            this.hideChatter = true;
        }
        else {
            this.hideChatter = false;
        }
        onMounted(() => {
            this._ShowHideRightPanel();
        });
    },
    _onHideRightPanel() {
        this.hideChatter = true;
        browser.localStorage.setItem("full_screen", true);
        this._ShowHideRightPanel();
    },

    _onShowRightPanel() {
        this.hideChatter = false;
        browser.localStorage.setItem("full_screen", false);
        this._ShowHideRightPanel();
    },

    _ShowHideRightPanel() {
        var $parent = $('span.hide-right-panel').parent();

        $('div.o_list_renderer').css('width', '');

        if(this.hideChatter) {
            $('span.hide-right-panel').addClass('d-none');
            $('span.show-right-panel').removeClass('d-none');
            if ($('div.o_form_sheet').length) {
                $('div.o_form_sheet').addClass('full-screen-form');
            }
            if ($('div.o_form_sheet_bg').length) {
                $('div.o_form_sheet_bg').next().addClass('d-none');
            }
        }
        else {
            $('span.show-right-panel').addClass('d-none');
            $('span.hide-right-panel').removeClass('d-none');
            if ($('div.o_form_sheet').length) {
                $('div.o_form_sheet').removeClass('full-screen-form');
            }
            if ($('div.o_form_sheet_bg').length) {
                $('div.o_form_sheet_bg').next().removeClass('d-none');
            }
        }
    },
});