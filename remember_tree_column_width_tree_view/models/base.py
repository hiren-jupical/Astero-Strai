from odoo import api, models

from lxml import etree


class Model(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def get_views(self, views, options=None):
        result = super(Model, self).get_views(views, options)

        result = self._update_column_width_field(views, result)
        result = self._update_column_width_field_one2many(views, result)

        return result

    def _update_column_width_field(self, views, list_view):
        for view in views:
            view_name = view[1]
            if view_name == 'list' and view_name in list_view['views']:
                viewObj = list_view['views'][view_name]
                view_id = viewObj['id']
                tree = etree.fromstring(viewObj['arch'])

                for node in tree.xpath('//field'):
                    field_name = node.get('name')
                    fieldOption = self.env.user.column_field_width_lines.filtered(lambda s:
                                                                             s.view_id.id == view_id
                                                                             and s.field_name == field_name
                                                                             and s.user_id.id == self.env.uid)
                    if fieldOption:
                        node.set('column_width', str(fieldOption.width))

                viewObj['arch'] = etree.tostring(tree, encoding="unicode").replace('\t', '')

        return list_view

    def _update_column_width_field_one2many(self, views, list_view):
        for view in views:
            view_name = view[1]
            if view_name in list_view['views']:
                if view_name == 'form':
                    viewObj = list_view['views'][view_name]
                    view_id = viewObj['id']
                    form = etree.fromstring(viewObj['arch'])
                    tree_nodes = form.xpath('//tree')
                    for tree in tree_nodes:
                        for node in tree.xpath('.//field'):
                            field_name = node.get('name')
                            fieldOption = self.env.user.column_field_width_lines.filtered(lambda s:
                                                                                    s.view_id.id == view_id
                                                                                    and s.field_name == field_name
                                                                                    and s.user_id.id == self.env.uid)

                            if fieldOption:
                                node.set('column_width', str(fieldOption.width))

                    viewObj['arch'] = etree.tostring(form, encoding="unicode").replace('\t', '')

        return list_view