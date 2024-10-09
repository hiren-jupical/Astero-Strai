from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestProductSupplierinfo(TransactionCase):
    def setUp(self):
        super().setUp()
        self.addCleanup(self.registry.reset_changes)
        self.addCleanup(self.registry.clear_all_caches)

        self.product = self.env['product.product'].create({'name': 'Testproduct', 'default_code': 'test_no_unique'})
        self.product2 = self.env['product.product'].create({'name': 'Testproduct2', 'default_code': 'test_no_unique2'})
        self.res_supplier = self.env['res.partner'].create({'name': 'TestSupplier', 'ref': 'TestSupplier'})
        self.res_supplier2 = self.env['res.partner'].create({'name': 'TestSupplier2', 'ref': 'TestSupplier2'})

    def test_duplicate_vendor_reference(self):
        self.assertEqual(len(self.product), 1)
        self.assertEqual(self.product.name, 'Testproduct')
        self.assertEqual(self.product.default_code, 'test_no_unique')  # could be set to a running number from another module. Check that this is not the case

        self.assertEqual(len(self.product2), 1)
        self.assertEqual(self.product2.name, 'Testproduct2')
        self.assertEqual(self.product2.default_code, 'test_no_unique2')

        # create a supplier for testing purposes
        # assert that there is only one available
        self.assertEqual(len(self.res_supplier), 1)
        self.assertEqual(self.res_supplier.name, 'TestSupplier')
        self.assertEqual(self.res_supplier.ref, 'TestSupplier')

        # create a product.supplierinfo for this product
        self.env['product.supplierinfo'].create({
            'partner_id': self.res_supplier.id,
            'product_code': 'test_no_unique',
            'product_id': self.product.id,
            'company_id': 1
        })

        # create a product.supplierinfo for the second product, using same vendor and vendor reference
        # this should result in a validation error
        with self.assertRaises(ValidationError, msg='Duplicate vendor reference'):
            self.env['product.supplierinfo'].create({
                'partner_id': self.res_supplier.id,
                'product_code': 'test_no_unique',
                'product_id': self.product2.id,
                'company_id': 1
            })

        # should work to use same supplier on same product with different product code
        self.env['product.supplierinfo'].create({
            'partner_id': self.res_supplier.id,
            'product_code': 'test_unique',
            'product_id': self.product2.id,
            'company_id': 1
        })

        # should work to use same product code when different supplier
        self.assertEqual(self.res_supplier2.name, 'TestSupplier2')
        self.assertEqual(self.res_supplier2.ref, 'TestSupplier2')
        self.env['product.supplierinfo'].create({
            'partner_id': self.res_supplier2.id,
            'product_code': 'test_unique',
            'product_id': self.product2.id,
            'company_id': 1
        })

        # should work to use same product / supplier / reference in a different company
        self.env['product.supplierinfo'].create({
            'partner_id': self.res_supplier2.id,
            'product_code': 'test_unique',
            'product_id': self.product2.id,
            'company_id': 2
        })