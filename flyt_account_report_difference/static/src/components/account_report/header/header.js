/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { AccountReportHeader } from "@account_reports/components/account_report/header/header";
import { _t } from "@web/core/l10n/translation";

patch(AccountReportHeader.prototype, {
    currentRoundingUnitName(roundingUnit) {
        // Need to get a current rounding filter name
        return _t("In %s", this.controller.options['rounding_unit_names'][roundingUnit]);
    }
});