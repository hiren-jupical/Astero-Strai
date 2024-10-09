/** @odoo-module */
import { useService } from "@web/core/utils/hooks";

import { Component, onWillStart } from "@odoo/owl";

export class SaleDashBoard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        onWillStart(async () => {
            this.saleData = await this.orm.call(
                "sale.order",
                "retrieve_sale_dashboard",
                [this.env.config.actionId]
            );
        });
    }

    setSearchContext(ev) {
        let filter_name = ev.currentTarget.getAttribute("filter_name");
        let filters = filter_name.split(',');
        let searchItems = this.env.searchModel.getSearchItems((item) => filters.includes(item.name));
        this.env.searchModel.query = [];
        for (const item of searchItems){
            this.env.searchModel.toggleSearchItem(item.id);
        }
    }
}

SaleDashBoard.template = 'sale.SaleDashboard'
