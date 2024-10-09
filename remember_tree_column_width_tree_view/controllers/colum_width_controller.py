
from odoo import http
from odoo.http import request


class ColumWidthFieldController(http.Controller):

    @http.route('/save/column_width', type='json', auth='user')
    def get_org_chart(self, view_id, field_name, **kw):
        fields_list = field_name.split(';')
        fields_list = [field.strip() for field in fields_list]
        for field in fields_list:
            data = field.split(':')
            if len(data) == 2:
                fieldName = data[0].strip()
                width = data[1].strip()
                columnField = request.env.user.column_field_width_lines.filtered(lambda s:
                                                                           s.view_id.id == view_id
                                                                           and s.field_name == fieldName
                                                                           and s.user_id.id == request.env.uid)

                if not columnField:
                    request.env['column.field.width.user'].sudo().create({
                        'view_id': view_id,
                        'field_name': data[0].strip(),
                        'user_id': request.env.uid,
                        'width': int(width)
                    })
                else:
                    columnField.width = int(width)

        return True
