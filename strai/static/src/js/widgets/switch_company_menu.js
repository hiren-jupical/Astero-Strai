/** @odoo-module **/
import { SwitchCompanyItem } from "@web/webclient/switch_company_menu/switch_company_menu";

import { patch } from "@web/core/utils/patch";

// New Component
patch(SwitchCompanyItem.prototype, {
    toggleCompany(companyId) {
        this.logIntoCompany(companyId);
    },
});