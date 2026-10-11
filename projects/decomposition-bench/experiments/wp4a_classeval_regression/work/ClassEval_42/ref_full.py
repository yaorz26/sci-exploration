class Hotel:
    def __init__(self, name, rooms):
        self.name = name
        self.available_rooms = rooms
        # available_rooms = {room_type1: room_number1, room_type2: room_number2, ...}
        # available_rooms = {'single': 5, 'double': 3}
        self.booked_rooms = {}
        # booked_rooms = {room_type1: {name1: room_number1, name2: room_number2, ...}, room_type2: {...}, ...}
        # booked_rooms = {'single': {'name1': 2, 'name2':1}, 'double': {}}

    def book_room(self, room_type, room_number, name):
        # Check if there are any rooms of the specified type available
        if room_type not in self.available_rooms.keys():
            return False

        if room_number <= self.available_rooms[room_type]:
            # Book the room by adding it to the booked_rooms dictionary
            if room_type not in self.booked_rooms.keys():
                self.booked_rooms[room_type] = {}
            self.booked_rooms[room_type][name] = room_number
            self.available_rooms[room_type] -= room_number
            return "Success!"
        elif self.available_rooms[room_type] != 0:
            return self.available_rooms[room_type]
        else:
            return False

    def check_in(self, room_type, room_number, name):
        # Check if the room of the specified type and number is booked
        if room_type not in self.booked_rooms.keys():
            return False
        if name in self.booked_rooms[room_type]:
            if room_number > self.booked_rooms[room_type][name]:
                return False
            elif room_number == self.booked_rooms[room_type][name]:
                # Check in the room by removing it from the booked_rooms dictionary
                self.booked_rooms[room_type].pop(name)
            else:
                self.booked_rooms[room_type][name] -= room_number


    def check_out(self, room_type, room_number):
        if room_type in self.available_rooms:
            self.available_rooms[room_type] += room_number
        else:
            self.available_rooms[room_type] = room_number

    def get_available_rooms(self, room_type):
        return self.available_rooms[room_type]

import unittest


class HotelTestBookRoom(unittest.TestCase):
    def setUp(self):
        self.hotel = Hotel('peace hotel', {'single': 3, 'double': 2})

    def test_book_room_1(self):
        result = self.hotel.book_room('single', 2, 'guest 1')
        self.assertEqual(result, 'Success!')
        self.assertEqual(self.hotel.booked_rooms, {'single': {'guest 1': 2}})
        self.assertEqual(self.hotel.available_rooms, {'single': 1, 'double': 2})

    def test_book_room_2(self):
        result = self.hotel.book_room('triple', 2, 'guest 1')
        self.assertFalse(result)
        self.assertEqual(self.hotel.booked_rooms, {})
        self.assertEqual(self.hotel.available_rooms, {'single': 3, 'double': 2})

    def test_book_room_3(self):
        self.hotel.book_room('single', 2, 'guest 1')
        result = self.hotel.book_room('single', 2, 'guest 2')
        self.assertEqual(result, 1)
        self.assertEqual(self.hotel.booked_rooms, {'single': {'guest 1': 2}})
        self.assertEqual(self.hotel.available_rooms, {'single': 1, 'double': 2})

    def test_book_room_4(self):
        self.hotel.book_room('single', 2, 'guest 1')
        result = self.hotel.book_room('single', 1, 'guest 2')
        self.assertEqual(result, 'Success!')
        self.assertEqual(self.hotel.booked_rooms, {'single': {'guest 1': 2, 'guest 2': 1}})
        self.assertEqual(self.hotel.available_rooms, {'double': 2, 'single': 0})

    def test_book_room_5(self):
        self.hotel.book_room('single', 2, 'guest 1')
        result = self.hotel.book_room('single', 3, 'guest 2')
        self.assertEqual(result, 1)
        self.assertEqual(self.hotel.booked_rooms, {'single': {'guest 1': 2}})
        self.assertEqual(self.hotel.available_rooms, {'single': 1, 'double': 2})

    def test_book_room_6(self):
        self.hotel.book_room('single', 3, 'guest 1')
        result = self.hotel.book_room('single', 100, 'guest 1')
        self.assertFalse(result)


class HotelTestCheckIn(unittest.TestCase):
    def setUp(self):
        self.hotel = Hotel('Test Hotel', {'single': 3, 'double': 2})
        self.hotel.booked_rooms = {'single': {'guest 1': 2}, 'double': {'guest 2': 1}}

    def test_check_in_1(self):
        self.hotel.check_in('single', 1, 'guest 1')
        self.assertEqual(self.hotel.booked_rooms, {'single': {'guest 1': 1}, 'double': {'guest 2': 1}})

    def test_check_in_2(self):
        self.assertFalse(self.hotel.check_in('single', 3, 'guest 1'))
        self.assertEqual(self.hotel.booked_rooms, {'single': {'guest 1': 2}, 'double': {'guest 2': 1}})

    def test_check_in_3(self):
        self.assertFalse(self.hotel.check_in('double', 1, 'guest 1'))
        self.assertEqual(self.hotel.booked_rooms, {'single': {'guest 1': 2}, 'double': {'guest 2': 1}})

    def test_check_in_4(self):
        self.hotel.check_in('double', 1, 'guest 2')
        self.assertEqual(self.hotel.booked_rooms, {'double': {}, 'single': {'guest 1': 2}})

    def test_check_in_5(self):
        self.hotel.check_in('double', 2, 'guest 2')
        self.assertEqual(self.hotel.booked_rooms, {'double': {'guest 2': 1}, 'single': {'guest 1': 2}})

    def test_check_in_6(self):
        res = self.hotel.check_in('abc', 1, 'guest 1')
        self.assertFalse(res)


class HotelTestCheckOut(unittest.TestCase):
    def setUp(self):
        self.hotel = Hotel('Test Hotel', {'single': 3, 'double': 2})
        self.hotel.booked_rooms = {'single': {'guest 1': 2}, 'double': {'guest 2': 1}}

    def test_check_out_1(self):
        self.hotel.check_out('single', 1)
        self.assertEqual(self.hotel.available_rooms, {'single': 4, 'double': 2})
        self.assertEqual(self.hotel.booked_rooms, {'single': {'guest 1': 2}, 'double': {'guest 2': 1}})

    def test_check_out_2(self):
        self.hotel.check_out('single', 3)
        self.assertEqual(self.hotel.available_rooms, {'single': 6, 'double': 2})
        self.assertEqual(self.hotel.booked_rooms, {'single': {'guest 1': 2}, 'double': {'guest 2': 1}})

    def test_check_out_3(self):
        self.hotel.check_out('triple', 2)
        self.assertEqual(self.hotel.available_rooms, {'single': 3, 'double': 2, 'triple': 2})
        self.assertEqual(self.hotel.booked_rooms, {'single': {'guest 1': 2}, 'double': {'guest 2': 1}})

    def test_check_out_4(self):
        self.hotel.check_out('double', 1)
        self.assertEqual(self.hotel.available_rooms, {'single': 3, 'double': 3})
        self.assertEqual(self.hotel.booked_rooms, {'single': {'guest 1': 2}, 'double': {'guest 2': 1}})

    def test_check_out_5(self):
        self.hotel.check_out('double', 2)
        self.assertEqual(self.hotel.available_rooms, {'single': 3, 'double': 4})
        self.assertEqual(self.hotel.booked_rooms, {'single': {'guest 1': 2}, 'double': {'guest 2': 1}})


class HotelTestAvailableRooms(unittest.TestCase):
    def setUp(self):
        self.hotel = Hotel('Test Hotel', {'single': 3, 'double': 2, 'triple': 2})

    def test_get_available_rooms(self):
        result = self.hotel.get_available_rooms('single')
        self.assertEqual(result, 3)

    def test_get_available_rooms_2(self):
        self.hotel.book_room('single', 2, 'guest 1')
        result = self.hotel.get_available_rooms('single')
        self.assertEqual(result, 1)

    def test_get_available_rooms_3(self):
        self.hotel.book_room('single', 3, 'guest 1')
        result = self.hotel.get_available_rooms('single')
        self.assertEqual(result, 0)

    def test_get_available_rooms_4(self):
        self.hotel.book_room('single', 3, 'guest 1')
        result = self.hotel.get_available_rooms('double')
        self.assertEqual(result, 2)

    def test_get_available_rooms_5(self):
        self.hotel.book_room('single', 3, 'guest 1')
        result = self.hotel.get_available_rooms('triple')
        self.assertEqual(result, 2)


class HotelTestMain(unittest.TestCase):
    def setUp(self) -> None:
        self.hotel = Hotel('Test Hotel', {'single': 3, 'double': 2})

    def test_main(self):
        result = self.hotel.book_room('single', 2, 'guest 1')
        self.assertEqual(result, 'Success!')
        self.assertEqual(self.hotel.booked_rooms, {'single': {'guest 1': 2}})
        self.assertEqual(self.hotel.available_rooms, {'single': 1, 'double': 2})

        self.hotel.check_in('single', 2, 'guest 1')
        self.assertEqual(self.hotel.booked_rooms, {'single': {}})
        self.assertEqual(self.hotel.available_rooms, {'single': 1, 'double': 2})

        self.hotel.check_out('single', 2)
        self.assertEqual(self.hotel.available_rooms, {'single': 3, 'double': 2})

        self.assertEqual(self.hotel.get_available_rooms('single'), 3)

if __name__ == '__main__':
    unittest.main()
