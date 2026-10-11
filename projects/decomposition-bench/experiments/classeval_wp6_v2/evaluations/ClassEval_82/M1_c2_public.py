class StockPortfolioTracker:
    """
    This is a class as StockPortfolioTracker that allows to add stocks, remove stocks, buy stocks, sell stocks, calculate the total value of the portfolio, and obtain a summary of the portfolio.
    """

    def __init__(self, cash_balance):
        """
        Initialize the StockPortfolioTracker class with a cash balance and an empty portfolio.
        """
        self.portfolio = []
        self.cash_balance = cash_balance

    def add_stock(self, stock):
        """
        Add a stock to the portfolio.
        :param stock: a dictionary with keys "name", "price", and "quantity"
        """
        self.portfolio.append(stock)

    def remove_stock(self, stock):
        """
        Remove a stock from the portfolio.
        :param stock: a dictionary with keys "name", "price", and "quantity"
        """
        if stock in self.portfolio:
            self.portfolio.remove(stock)
            return True
        return False

    def buy_stock(self, stock, quantity):
        """
        Buy a stock and add it to the portfolio.
        :param stock: a dictionary with keys "name", "price", and "quantity"
        :param quantity: the quantity of the stock to buy, int.
        :return: True if the stock was bought successfully, False if the cash balance is not enough.
        """
        total_cost = stock['price'] * quantity
        if self.cash_balance >= total_cost:
            self.cash_balance -= total_cost
            stock['quantity'] = quantity
            self.portfolio.append(stock)
            return True
        return False

    def sell_stock(self, stock, quantity):
        """
        Sell a stock and remove it from the portfolio and add the cash to the cash balance.
        :param stock: a dictionary with keys "name", "price", and "quantity"
        :param quantity: the quantity of the stock to sell, int.
        :return: True if the stock was sold successfully, False if the quantity of the stock is not enough.
        """
        for s in self.portfolio:
            if s['name'] == stock['name']:
                if s['quantity'] >= quantity:
                    s['quantity'] -= quantity
                    if s['quantity'] == 0:
                        self.portfolio.remove(s)
                    self.cash_balance += stock['price'] * quantity
                    return True
        return False

    def calculate_portfolio_value(self):
        """
        Calculate the total value of the portfolio.
        :return: the total value of the portfolio, float.
        """
        total_value = 0
        for stock in self.portfolio:
            total_value += stock['price'] * stock['quantity']
        return total_value

    def get_portfolio_summary(self):
        """
        Get a summary of the portfolio.
        :return: a tuple of the total value of the portfolio and a list of dictionaries with keys "name" and "value"
        """
        total_value = self.calculate_portfolio_value()
        summary = []
        for stock in self.portfolio:
            value = stock['price'] * stock['quantity']
            summary.append({'name': stock['name'], 'value': value})
        return total_value, summary

    def get_stock_value(self, stock):
        """
        Get the value of a stock.
        :param stock: a dictionary with keys "name", "price", and "quantity"
        :return: the value of the stock, float.
        """
        return stock['price'] * stock['quantity']

import unittest


class StockPortfolioTrackerTestAddStock(unittest.TestCase):
    def test_add_stock(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.add_stock({"name": "AAPL", "price": 150.0, "quantity": 10})
        self.assertEqual(tracker.portfolio, [{'name': 'AAPL', 'price': 150.0, 'quantity': 10}])

    def test_add_stock_2(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 10}]
        tracker.add_stock({"name": "AAPL", "price": 150.0, "quantity": 10})
        self.assertEqual(tracker.portfolio, [{'name': 'AAPL', 'price': 150.0, 'quantity': 20}])

    def test_add_stock_3(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 10}]
        tracker.add_stock({"name": "MSFT", "price": 150.0, "quantity": 10})
        self.assertEqual(tracker.portfolio, [{'name': 'AAPL', 'price': 150.0, 'quantity': 10},
                                             {'name': 'MSFT', 'price': 150.0, 'quantity': 10}])

    def test_add_stock_4(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 10}]
        tracker.add_stock({"name": "AAPL", "price": 150.0, "quantity": 10})
        tracker.add_stock({"name": "MSFT", "price": 150.0, "quantity": 10})
        self.assertEqual(tracker.portfolio, [{'name': 'AAPL', 'price': 150.0, 'quantity': 20},
                                             {'name': 'MSFT', 'price': 150.0, 'quantity': 10}])

    def test_add_stock_5(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 10}]
        tracker.add_stock({"name": "AAPL", "price": 150.0, "quantity": 10})
        tracker.add_stock({"name": "MSFT", "price": 150.0, "quantity": 10})
        tracker.add_stock({"name": "MSFT", "price": 150.0, "quantity": 10})
        self.assertEqual(tracker.portfolio, [{'name': 'AAPL', 'price': 150.0, 'quantity': 20},
                                             {'name': 'MSFT', 'price': 150.0, 'quantity': 20}])


class StockPortfolioTrackerTestRemoveStock(unittest.TestCase):
    def test_remove_stock(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 10}]
        self.assertEqual(tracker.remove_stock({"name": "AAPL", "price": 150.0, "quantity": 10}), True)
        self.assertEqual(tracker.portfolio, [])

    def test_remove_stock_2(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 10},
                             {'name': 'MSFT', 'price': 150.0, 'quantity': 10}]
        self.assertEqual(tracker.remove_stock({"name": "AAPL", "price": 150.0, "quantity": 10}), True)
        self.assertEqual(tracker.portfolio, [{'name': 'MSFT', 'price': 150.0, 'quantity': 10}])

    def test_remove_stock_3(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 10},
                             {'name': 'MSFT', 'price': 150.0, 'quantity': 10}]
        self.assertEqual(tracker.remove_stock({"name": "MSFT", "price": 150.0, "quantity": 20}), False)
        self.assertEqual(tracker.portfolio, [{'name': 'AAPL', 'price': 150.0, 'quantity': 10},
                                             {'name': 'MSFT', 'price': 150.0, 'quantity': 10}])

    def test_remove_stock_4(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 10}]
        self.assertEqual(tracker.remove_stock({"name": "MSFT", "price": 150.0, "quantity": 10}), False)
        self.assertEqual(tracker.portfolio, [{'name': 'AAPL', 'price': 150.0, 'quantity': 10}])

    def test_remove_stock_5(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 10},
                             {'name': 'MSFT', 'price': 150.0, 'quantity': 10}]
        self.assertEqual(tracker.remove_stock({"name": "MSFT", "price": 150.0, "quantity": 10}), True)
        self.assertEqual(tracker.portfolio, [{'name': 'AAPL', 'price': 150.0, 'quantity': 10}])


class StockPortfolioTrackerTestBuyStock(unittest.TestCase):
    def test_buy_stock(self):
        tracker = StockPortfolioTracker(10000.0)
        self.assertEqual(tracker.buy_stock({"name": "AAPL", "price": 150.0, "quantity": 10}), True)
        self.assertEqual(tracker.portfolio, [{'name': 'AAPL', 'price': 150.0, 'quantity': 10}])
        self.assertEqual(tracker.cash_balance, 8500.0)

    def test_buy_stock_2(self):
        tracker = StockPortfolioTracker(1000.0)
        self.assertEqual(tracker.buy_stock({"name": "AAPL", "price": 150.0, "quantity": 10}), False)
        self.assertEqual(tracker.portfolio, [])
        self.assertEqual(tracker.cash_balance, 1000.0)

    def test_buy_stock_3(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 10}]
        self.assertEqual(tracker.buy_stock({"name": "AAPL", "price": 150.0, "quantity": 10}), True)
        self.assertEqual(tracker.portfolio, [{'name': 'AAPL', 'price': 150.0, 'quantity': 20}])
        self.assertEqual(tracker.cash_balance, 8500.0)

    def test_buy_stock_4(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 10}]
        self.assertEqual(tracker.buy_stock({"name": "MSFT", "price": 150.0, "quantity": 10}), True)
        self.assertEqual(tracker.buy_stock({"name": "MSFT", "price": 150.0, "quantity": 10}), True)
        self.assertEqual(tracker.portfolio, [{'name': 'AAPL', 'price': 150.0, 'quantity': 10},
                                             {'name': 'MSFT', 'price': 150.0, 'quantity': 20}])
        self.assertEqual(tracker.cash_balance, 7000.0)

    def test_buy_stock_5(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 10}]
        self.assertEqual(tracker.buy_stock({"name": "AAPL", "price": 150.0, "quantity": 10}), True)
        self.assertEqual(tracker.buy_stock({"name": "MSFT", "price": 150.0, "quantity": 10}), True)
        self.assertEqual(tracker.portfolio, [{'name': 'AAPL', 'price': 150.0, 'quantity': 20},
                                             {'name': 'MSFT', 'price': 150.0, 'quantity': 10}])
        self.assertEqual(tracker.cash_balance, 7000.0)


class StockPortfolioTrackerTestSellStock(unittest.TestCase):
    def test_sell_stock(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 10}]
        self.assertEqual(tracker.sell_stock({"name": "AAPL", "price": 150.0, "quantity": 9}), True)
        self.assertEqual(tracker.portfolio, [{"name": "AAPL", "price": 150.0, "quantity": 1}])
        self.assertEqual(tracker.cash_balance, 11350.0)

    def test_sell_stock_2(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 10}]
        self.assertEqual(tracker.sell_stock({"name": "AAPL", "price": 150.0, "quantity": 20}), False)
        self.assertEqual(tracker.portfolio, [{"name": "AAPL", "price": 150.0, "quantity": 10}])
        self.assertEqual(tracker.cash_balance, 10000.0)

    def test_sell_stock_3(self):
        tracker = StockPortfolioTracker(10000.0)
        self.assertEqual(tracker.sell_stock({"name": "AAPL", "price": 150.0, "quantity": 10}), False)
        self.assertEqual(tracker.portfolio, [])
        self.assertEqual(tracker.cash_balance, 10000.0)

    def test_sell_stock_4(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 20}]
        self.assertEqual(tracker.sell_stock({"name": "AAPL", "price": 150.0, "quantity": 20}), True)
        self.assertEqual(tracker.portfolio, [])
        self.assertEqual(tracker.cash_balance, 13000.0)

    def test_sell_stock_5(self):
        tracker = StockPortfolioTracker(10000.0)
        tracker.portfolio = [{'name': 'AAPL', 'price': 150.0, 'quantity': 20},
                             {'name': 'MSFT', 'price': 150.0, 'quantity': 10}]
        self.assertEqual(tracker.sell_stock({"name": "AAPL", "price": 150.0, "quantity": 20}), True)
        self.assertEqual(tracker.portfolio, [{'name': 'MSFT', 'price': 150.0, 'quantity': 10}])
        self.assertEqual(tracker.cash_balance, 13000.0)

if __name__ == '__main__':
    unittest.main()
