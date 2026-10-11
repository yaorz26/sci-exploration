import unittest

class WarehouseTestAddProduct(unittest.TestCase):
    def test_add_product_1(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        self.assertEqual(warehouse.inventory, {1: {'name': 'product 1', 'quantity': 10}})

    def test_add_product_2(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        warehouse.add_product(2, 'product 2', 5)
        self.assertEqual(warehouse.inventory,
                         {1: {'name': 'product 1', 'quantity': 10}, 2: {'name': 'product 2', 'quantity': 5}})

    def test_add_product_3(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 3', 10)
        self.assertEqual(warehouse.inventory, {1: {'name': 'product 3', 'quantity': 10}})

    def test_add_product_4(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 4', 10)
        self.assertEqual(warehouse.inventory, {1: {'name': 'product 4', 'quantity': 10}})

    def test_add_product_5(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 5', 10)
        self.assertEqual(warehouse.inventory, {1: {'name': 'product 5', 'quantity': 10}})

    def test_add_product_6(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 5', 10)
        warehouse.add_product(1, 'product 5', 10)
        self.assertEqual(warehouse.inventory, {1: {'name': 'product 5', 'quantity': 20}})


class WarehouseTestUpdateProductQuantity(unittest.TestCase):
    def test_update_product_quantity_1(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        warehouse.update_product_quantity(1, 5)
        self.assertEqual(warehouse.inventory, {1: {'name': 'product 1', 'quantity': 15}})

    # quantity is negative
    def test_update_product_quantity_2(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        warehouse.update_product_quantity(1, -5)
        self.assertEqual(warehouse.inventory, {1: {'name': 'product 1', 'quantity': 5}})

    def test_update_product_quantity_3(self):
        warehouse = Warehouse()
        warehouse.update_product_quantity(1, -5)
        self.assertEqual(warehouse.inventory, {})

    def test_update_product_quantity_4(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        warehouse.update_product_quantity(1, 1)
        self.assertEqual(warehouse.inventory, {1: {'name': 'product 1', 'quantity': 11}})

    def test_update_product_quantity_5(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        warehouse.update_product_quantity(1, -9)
        self.assertEqual(warehouse.inventory, {1: {'name': 'product 1', 'quantity': 1}})


class WarehouseTestGetProductQuantity(unittest.TestCase):
    def test_get_product_quantity_1(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        self.assertEqual(warehouse.get_product_quantity(1), 10)

    def test_get_product_quantity_2(self):
        warehouse = Warehouse()
        self.assertEqual(warehouse.get_product_quantity(1), False)

    def test_get_product_quantity_3(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 5)
        self.assertEqual(warehouse.get_product_quantity(1), 5)

    def test_get_product_quantity_4(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 100)
        self.assertEqual(warehouse.get_product_quantity(1), 100)

    def test_get_product_quantity_5(self):
        warehouse = Warehouse()
        warehouse.add_product(5, 'product 1', 10)
        self.assertEqual(warehouse.get_product_quantity(5), 10)

