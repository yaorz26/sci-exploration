import time

class Thermostat:
    def __init__(self, current_temperature, target_temperature, mode):
        self.current_temperature = current_temperature
        self.target_temperature = target_temperature
        self.mode = mode

    def get_target_temperature(self):
        return self.target_temperature

    def set_target_temperature(self, temperature):
        self.target_temperature = temperature

    def get_mode(self):
        return self.mode

    def set_mode(self, mode):
        if mode in ['heat', 'cool']:
            self.mode = mode
        else:
            return False

    def auto_set_mode(self):
        if self.current_temperature < self.target_temperature:
            self.mode = 'heat'
        else:
            self.mode = 'cool'

    def auto_check_conflict(self):
        if self.current_temperature > self.target_temperature:
            if self.mode == 'cool':
                return True
            else:
                self.auto_set_mode()
                return False
        else:
            if self.mode == 'heat':
                return True
            else:
                self.auto_set_mode()
                return False

    def simulate_operation(self):
        self.auto_set_mode()
        use_time = 0
        if self.mode == 'heat':
            while(self.current_temperature < self.target_temperature):
                self.current_temperature += 1
                use_time += 1
        else:
            while(self.current_temperature > self.target_temperature):
                self.current_temperature -= 1
                use_time += 1
        return use_time

import unittest

class ThermostatTestGetTargetTemperature(unittest.TestCase):
    def test_get_target_temperature_1(self):
        t = Thermostat(20, 25, 'heat')
        self.assertEqual(t.get_target_temperature(), 25)

    def test_get_target_temperature_2(self):
        t = Thermostat(20, 25, 'cool')
        self.assertEqual(t.get_target_temperature(), 25)

    def test_get_target_temperature_3(self):
        t = Thermostat(20, 25, 'test')
        self.assertEqual(t.get_target_temperature(), 25)

    def test_get_target_temperature_4(self):
        t = Thermostat(25, 25, 'cool')
        self.assertEqual(t.get_target_temperature(), 25)

    def test_get_target_temperature_5(self):
        t = Thermostat(25, 25, 'heat')
        self.assertEqual(t.get_target_temperature(), 25)


class ThermostatTestSetTargetTemperature(unittest.TestCase):
    def test_set_target_temperature_1(self):
        t = Thermostat(20, 25, 'heat')
        t.set_target_temperature(30)
        self.assertEqual(t.get_target_temperature(), 30)

    def test_set_target_temperature_2(self):
        t = Thermostat(20, 25, 'cool')
        t.set_target_temperature(10)
        self.assertEqual(t.get_target_temperature(), 10)

    def test_set_target_temperature_3(self):
        t = Thermostat(20, 25, 'test')
        t.set_target_temperature(10)
        self.assertEqual(t.get_target_temperature(), 10)

    def test_set_target_temperature_4(self):
        t = Thermostat(25, 25, 'cool')
        t.set_target_temperature(10)
        self.assertEqual(t.get_target_temperature(), 10)

    def test_set_target_temperature_5(self):
        t = Thermostat(25, 25, 'heat')
        t.set_target_temperature(10)
        self.assertEqual(t.get_target_temperature(), 10)


class ThermostatTestGetMode(unittest.TestCase):
    def test_get_mode_1(self):
        t = Thermostat(20, 25, 'heat')
        self.assertEqual(t.get_mode(), 'heat')

    def test_get_mode_2(self):
        t = Thermostat(20, 25, 'cool')
        self.assertEqual(t.get_mode(), 'cool')

    def test_get_mode_3(self):
        t = Thermostat(20, 25, 'test')
        self.assertEqual(t.get_mode(), 'test')

    def test_get_mode_4(self):
        t = Thermostat(25, 25, 'cool')
        self.assertEqual(t.get_mode(), 'cool')

    def test_get_mode_5(self):
        t = Thermostat(25, 25, 'heat')
        self.assertEqual(t.get_mode(), 'heat')


class ThermostatTestSetMode(unittest.TestCase):
    def test_set_mode_1(self):
        t = Thermostat(20, 25, 'heat')
        t.set_mode('cool')
        self.assertEqual(t.get_mode(), 'cool')

    # use mode that not in ['heat', 'cool']
    def test_set_mode_2(self):
        t = Thermostat(20, 25, 'heat')
        self.assertFalse(t.set_mode('test'))

    def test_set_mode_3(self):
        t = Thermostat(20, 25, 'cool')
        t.set_mode('heat')
        self.assertEqual(t.get_mode(), 'heat')

    def test_set_mode_4(self):
        t = Thermostat(20, 25, 'test')
        t.set_mode('heat')
        self.assertEqual(t.get_mode(), 'heat')

    def test_set_mode_5(self):
        t = Thermostat(25, 25, 'cool')
        t.set_mode('heat')
        self.assertEqual(t.get_mode(), 'heat')


class ThermostatTestAutoSetMode(unittest.TestCase):
    def test_auto_set_mode_1(self):
        t = Thermostat(20, 25, 'heat')
        t.auto_set_mode()
        self.assertEqual(t.get_mode(), 'heat')

    def test_auto_set_mode_2(self):
        t = Thermostat(25, 20, 'heat')
        t.auto_set_mode()
        self.assertEqual(t.get_mode(), 'cool')

    def test_auto_set_mode_3(self):
        t = Thermostat(25, 20, 'cool')
        t.auto_set_mode()
        self.assertEqual(t.get_mode(), 'cool')

    def test_auto_set_mode_4(self):
        t = Thermostat(20, 25, 'cool')
        t.auto_set_mode()
        self.assertEqual(t.get_mode(), 'heat')

    def test_auto_set_mode_5(self):
        t = Thermostat(25, 25, 'cool')
        t.auto_set_mode()
        self.assertEqual(t.get_mode(), 'cool')

class ThermostatTestAutoCheckConflict(unittest.TestCase):
    def test_auto_check_conflict_1(self):
        t = Thermostat(30, 25, 'cool')
        self.assertTrue(t.auto_check_conflict())

    def test_auto_check_conflict_2(self):
        t = Thermostat(30, 25, 'heat')
        self.assertFalse(t.auto_check_conflict())
        self.assertEqual(t.mode, 'cool')

    def test_auto_check_conflict_3(self):
        t = Thermostat(25, 30, 'heat')
        self.assertTrue(t.auto_check_conflict())

    def test_auto_check_conflict_4(self):
        t = Thermostat(25, 30, 'cool')
        self.assertFalse(t.auto_check_conflict())
        self.assertEqual(t.mode, 'heat')

    def test_auto_check_conflict_5(self):
        t = Thermostat(25, 25, 'cool')
        self.assertFalse(t.auto_check_conflict())
        self.assertEqual(t.mode, 'cool')


class ThermostatTestSimulateOperation(unittest.TestCase):
    def test_simulate_operation_1(self):
        t = Thermostat(20, 25, 'heat')
        self.assertEqual(t.simulate_operation(), 5)
        self.assertEqual(t.get_mode(), 'heat')
        self.assertEqual(t.current_temperature, 25)

    def test_simulate_operation_2(self):
        t = Thermostat(25.7, 20, 'cool')
        self.assertEqual(t.simulate_operation(), 6)
        self.assertEqual(t.get_mode(), 'cool')
        self.assertEqual(t.current_temperature, 19.7)

    def test_simulate_operation_3(self):
        t = Thermostat(25, 25, 'heat')
        self.assertEqual(t.simulate_operation(), 0)
        self.assertEqual(t.get_mode(), 'cool')
        self.assertEqual(t.current_temperature, 25)

    def test_simulate_operation_4(self):
        t = Thermostat(25, 25, 'cool')
        self.assertEqual(t.simulate_operation(), 0)
        self.assertEqual(t.get_mode(), 'cool')
        self.assertEqual(t.current_temperature, 25)

    def test_simulate_operation_5(self):
        t = Thermostat(25, 25, 'test')
        self.assertEqual(t.simulate_operation(), 0)
        self.assertEqual(t.get_mode(), 'cool')
        self.assertEqual(t.current_temperature, 25)

class ThermostatTestMain(unittest.TestCase):
    def test_main(self):
        t = Thermostat(20, 37.5, 'cool')
        self.assertEqual(t.get_target_temperature(), 37.5)

        t.set_target_temperature(37.6)
        self.assertEqual(t.target_temperature, 37.6)

        self.assertEqual(t.get_mode(), 'cool')
        self.assertFalse(t.set_mode('test'))

        self.assertFalse(t.auto_check_conflict())
        self.assertEqual(t.get_mode(), 'heat')
        self.assertEqual(t.simulate_operation(), 18)

if __name__ == '__main__':
    unittest.main()
