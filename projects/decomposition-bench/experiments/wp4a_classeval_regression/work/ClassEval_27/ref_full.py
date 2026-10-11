class CurrencyConverter:
    def __init__(self):
        self.rates = {
            'USD': 1.0,
            'EUR': 0.85,
            'GBP': 0.72,
            'JPY': 110.15,
            'CAD': 1.23,
            'AUD': 1.34,
            'CNY': 6.40,
        }

    def convert(self, amount, from_currency, to_currency):
        if from_currency == to_currency:
            return amount

        if from_currency not in self.rates or to_currency not in self.rates:
            return False

        from_rate = self.rates[from_currency]
        to_rate = self.rates[to_currency]

        converted_amount = (amount / from_rate) * to_rate
        return converted_amount

    def get_supported_currencies(self):
        return list(self.rates.keys())

    def add_currency_rate(self, currency, rate):
        if currency in self.rates:
            return False
        self.rates[currency] = rate

    def update_currency_rate(self, currency, new_rate):
        if currency not in self.rates:
            return False
        self.rates[currency] = new_rate

import unittest


class CurrencyConverterTestConvert(unittest.TestCase):
    def test_convert_1(self):
        cc = CurrencyConverter()
        res = cc.convert(64, 'CNY', 'USD')
        self.assertEqual(res, 10.0)

    def test_convert_2(self):
        cc = CurrencyConverter()
        res = cc.convert(64, 'USD', 'USD')
        self.assertEqual(res, 64)

    def test_convert_3(self):
        cc = CurrencyConverter()
        res = cc.convert(64, 'CNY', 'GBP')
        self.assertAlmostEqual(res, 7.1999999999999)

    def test_convert_4(self):
        cc = CurrencyConverter()
        res = cc.convert(64, 'USD', 'GBP')
        self.assertAlmostEqual(res, 46.08)

    def test_convert_5(self):
        cc = CurrencyConverter()
        res = cc.convert(64, 'USD', 'CAD')
        self.assertAlmostEqual(res, 78.72)

    def test_convert_6(self):
        cc = CurrencyConverter()
        res = cc.convert(64, '???', 'USD')
        self.assertFalse(res)


class CurrencyConverterTestGetSupportedCurrencies(unittest.TestCase):
    def test_get_supported_currencies_1(self):
        cc = CurrencyConverter()
        res = cc.get_supported_currencies()
        self.assertEqual(res, ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CNY'])

    def test_get_supported_currencies_2(self):
        cc = CurrencyConverter()
        res = cc.get_supported_currencies()
        self.assertEqual(res, ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CNY'])

    def test_get_supported_currencies_3(self):
        cc = CurrencyConverter()
        res = cc.get_supported_currencies()
        self.assertEqual(res, ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CNY'])

    def test_get_supported_currencies_4(self):
        cc = CurrencyConverter()
        res = cc.get_supported_currencies()
        self.assertEqual(res, ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CNY'])

    def test_get_supported_currencies_5(self):
        cc = CurrencyConverter()
        res = cc.get_supported_currencies()
        self.assertEqual(res, ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CNY'])


class CurrencyConverterTestAddCurrencyRate(unittest.TestCase):
    def test_add_currency_rate_1(self):
        cc = CurrencyConverter()
        cc.add_currency_rate('KRW', 1308.84)
        self.assertEqual(cc.rates['KRW'], 1308.84)

    def test_add_currency_rate_2(self):
        cc = CurrencyConverter()
        cc.add_currency_rate('aaa', 1.0)
        self.assertEqual(cc.rates['aaa'], 1.0)

    def test_add_currency_rate_3(self):
        cc = CurrencyConverter()
        cc.add_currency_rate('bbb', 2.0)
        self.assertEqual(cc.rates['bbb'], 2.0)

    def test_add_currency_rate_4(self):
        cc = CurrencyConverter()
        cc.add_currency_rate('ccc', 3.0)
        self.assertEqual(cc.rates['ccc'], 3.0)

    def test_add_currency_rate_5(self):
        cc = CurrencyConverter()
        cc.add_currency_rate('ddd', 4.0)
        self.assertEqual(cc.rates['ddd'], 4.0)

    def test_add_currency_rate_6(self):
        cc = CurrencyConverter()
        res = cc.add_currency_rate('USD', 1.0)
        self.assertFalse(res)


class CurrencyConverterTestUpdateCurrencyRate(unittest.TestCase):
    def test_update_currency_rate_1(self):
        cc = CurrencyConverter()
        cc.update_currency_rate('CNY', 7.18)
        self.assertEqual(cc.rates['CNY'], 7.18)

    def test_update_currency_rate_2(self):
        cc = CurrencyConverter()
        cc.update_currency_rate('CNY', 1.0)
        self.assertEqual(cc.rates['CNY'], 1.0)

    def test_update_currency_rate_3(self):
        cc = CurrencyConverter()
        cc.update_currency_rate('CNY', 2.0)
        self.assertEqual(cc.rates['CNY'], 2.0)

    def test_update_currency_rate_4(self):
        cc = CurrencyConverter()
        cc.update_currency_rate('CNY', 3.0)
        self.assertEqual(cc.rates['CNY'], 3.0)

    def test_update_currency_rate_5(self):
        cc = CurrencyConverter()
        cc.update_currency_rate('CNY', 4.0)
        self.assertEqual(cc.rates['CNY'], 4.0)

    def test_update_currency_rate_6(self):
        cc = CurrencyConverter()
        res = cc.update_currency_rate('???', 7.18)
        self.assertFalse(res)


class CurrencyConverterTest(unittest.TestCase):
    def test_currencyconverter(self):
        cc = CurrencyConverter()
        res = cc.convert(64, 'CNY', 'USD')
        self.assertEqual(res, 10.0)
        res = cc.get_supported_currencies()
        self.assertEqual(res, ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CNY'])
        cc.add_currency_rate('KRW', 1308.84)
        self.assertEqual(cc.rates['KRW'], 1308.84)
        cc.update_currency_rate('CNY', 7.18)
        self.assertEqual(cc.rates['CNY'], 7.18)

if __name__ == '__main__':
    unittest.main()
