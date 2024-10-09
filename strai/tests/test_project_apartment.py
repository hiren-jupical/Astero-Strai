from odoo.tests import TransactionCase, tagged


class TestProjectApartment(TransactionCase):
    def setUp(self):
        super().setUp()
        self.addCleanup(self.registry.reset_changes)
        self.addCleanup(self.registry.clear_caches)

        self.builder = self.env['res.partner'].create({
            'name': 'Builder',
            'is_builder': True
        })

        self.project = self.env['sales.projects'].create({
            'name': 'TestProject',
            'developer_id': self.builder.id
        })

        self.apartment = self.env['sales.projects.apartment'].create({
            'name': 'TestApartment',
            'sales_project_id': self.project.id
        })

    def test_project_autocreate_analytic_plan(self):
        self.assertIsNotNone(self.project.account_group_id)
        self.assertEqual(self.project.account_group_id.name, self.project.name)

    def test_apartment_autocreate_analytic_account(self):
        self.assertIsNotNone(self.apartment.analytic_account_id)
        self.assertEqual(self.apartment.analytic_account_id.name, self.apartment.name)
