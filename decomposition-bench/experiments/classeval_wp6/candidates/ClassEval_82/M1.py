class StockPortfolioTracker:
    def __init__(self, cash_balance):
        self.portfolio = []
        self.cash_balance = cash_balance

    def add_stock(self, stock):
        self.portfolio.append(stock)

    def remove_stock(self, stock):
        for i, s in enumerate(self.portfolio):
            if s == stock:
                del self.portfolio[i]
                return True
        return False

    def buy_stock(self, stock, quantity):
        total_cost = stock['price'] * quantity
        if self.cash_balance >= total_cost:
            self.cash_balance -= total_cost
            stock['quantity'] += quantity
            return True
        return False

    def sell_stock(self, stock, quantity):
        for i, s in enumerate(self.portfolio):
            if s == stock:
                if s['quantity'] >= quantity:
                    s['quantity'] -= quantity
                    self.cash_balance += stock['price'] * quantity
                    if s['quantity'] == 0:
                        del self.portfolio[i]
                    return True
                return False
        return False

    def calculate_portfolio_value(self):
        return sum(s['price'] * s['quantity'] for s in self.portfolio)

    def get_portfolio_summary(self):
        total_value = self.calculate_portfolio_value()
        summary = [{'name': s['name'], 'value': s['price'] * s['quantity']} for s in self.portfolio]
        return total_value, summary

    def get_stock_value(self, stock):
        for s in self.portfolio:
            if s == stock:
                return s['price'] * s['quantity']
        return 0