import unittest

class WarehouseTestCreateOrder(unittest.TestCase):
    def test_create_order_1(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        warehouse.create_order(1, 1, 5)
        self.assertEqual(warehouse.orders, {1: {'product_id': 1, 'quantity': 5, 'status': 'Shipped'}})

    def test_create_order_2(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        result = warehouse.create_order(1, 1, 15)
        self.assertFalse(result)

    def test_create_order_3(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 1)
        warehouse.create_order(1, 1, 1)
        self.assertEqual(warehouse.orders, {1: {'product_id': 1, 'quantity': 1, 'status': 'Shipped'}})

    def test_create_order_4(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 4', 5)
        warehouse.create_order(1, 1, 5)
        self.assertEqual(warehouse.orders, {1: {'product_id': 1, 'quantity': 5, 'status': 'Shipped'}})

    def test_create_order_5(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 5', 100)
        warehouse.create_order(1, 1, 50)
        self.assertEqual(warehouse.orders, {1: {'product_id': 1, 'quantity': 50, 'status': 'Shipped'}})


class WarehouseTestChangeOrderStatus(unittest.TestCase):
    def test_change_order_status_1(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        warehouse.create_order(1, 1, 5)
        warehouse.change_order_status(1, 'Delivered')
        self.assertEqual(warehouse.orders, {1: {'product_id': 1, 'quantity': 5, 'status': 'Delivered'}})

    def test_change_order_status_2(self):
        warehouse = Warehouse()
        result = warehouse.change_order_status(1, 'Delivered')
        self.assertFalse(result)

    def test_change_order_status_3(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 3', 5)
        warehouse.create_order(1, 1, 5)
        warehouse.change_order_status(1, 'Delivered')
        self.assertEqual(warehouse.orders, {1: {'product_id': 1, 'quantity': 5, 'status': 'Delivered'}})

    def test_change_order_status_4(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 4', 100)
        warehouse.create_order(1, 1, 50)
        warehouse.change_order_status(1, 'Delivered')
        self.assertEqual(warehouse.orders, {1: {'product_id': 1, 'quantity': 50, 'status': 'Delivered'}})

    def test_change_order_status_5(self):
        warehouse = Warehouse()
        result = warehouse.change_order_status(2, 'Delivered')
        self.assertFalse(result)


class WarehouseTestTrackOrder(unittest.TestCase):
    def test_track_order_1(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        warehouse.create_order(1, 1, 5)
        self.assertEqual(warehouse.track_order(1), 'Shipped')

    def test_track_order_2(self):
        warehouse = Warehouse()
        result = warehouse.track_order(1)
        self.assertFalse(result)

    def test_track_order_3(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 3', 10)
        warehouse.create_order(1, 1, 1)
        self.assertEqual(warehouse.track_order(1), 'Shipped')

    def test_track_order_4(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 4', 100)
        warehouse.create_order(1, 1, 50)
        self.assertEqual(warehouse.track_order(1), 'Shipped')

    def test_track_order_5(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 5', 100)
        warehouse.create_order(1, 1, 10)
        self.assertEqual(warehouse.track_order(1), 'Shipped')


class WarehouseTestMain(unittest.TestCase):
    def test_main(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        self.assertEqual({1: {'name': 'product 1', 'quantity': 10}}, warehouse.inventory)

        warehouse.update_product_quantity(1, -5)
        self.assertEqual({1: {'name': 'product 1', 'quantity': 5}}, warehouse.inventory)

        self.assertEqual(warehouse.get_product_quantity(1), 5)

        warehouse.create_order(1, 1, 3)
        self.assertEqual({1: {'product_id': 1, 'quantity': 3, 'status': 'Shipped'}}, warehouse.orders)

        warehouse.change_order_status(1, 'Delivered')
        self.assertEqual({1: {'product_id': 1, 'quantity': 3, 'status': 'Delivered'}}, warehouse.orders)

        self.assertEqual('Delivered', warehouse.track_order(1))