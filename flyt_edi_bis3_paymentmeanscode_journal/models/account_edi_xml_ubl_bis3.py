from odoo import models, _

class AccountEdiXmlUBLBIS3(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_bis3"

    def _get_invoice_payment_means_vals_list(self, invoice):

        vals_list = super(AccountEdiXmlUBLBIS3, self)._get_invoice_payment_means_vals_list(invoice)

        new_payment_means_code = invoice.journal_id.payment_means_code_edi_bis3

        if new_payment_means_code:
            new_payment_means_code_selection = self.env['account.journal']._fields['payment_means_code_edi_bis3'].selection
            new_payment_means_code_description = next((desc for code, desc in new_payment_means_code_selection if code == new_payment_means_code), None)

            for item in vals_list:
                if 'payment_means_code' in item:

                    item['payment_means_code'] = new_payment_means_code

                    if 'payment_means_code_attrs' in item and new_payment_means_code_description:
                        item['payment_means_code_attrs']['name'] = new_payment_means_code_description

        return vals_list
