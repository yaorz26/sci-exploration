from datetime import datetime

class Chat:
    def __init__(self):
        self.users = {}

    def add_user(self, username):
        if username in self.users:
            return False
        else:
            self.users[username] = []
            return True

    def remove_user(self, username):
        if username in self.users:
            del self.users[username]
            return True
        else:
            return False

    def send_message(self, sender, receiver, message):
        if sender not in self.users or receiver not in self.users:
            return False

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_info = {
            'sender': sender,
            'receiver': receiver,
            'message': message,
            'timestamp': timestamp
        }
        self.users[sender].append(message_info)
        self.users[receiver].append(message_info)
        return True

    def get_messages(self, username):
        if username not in self.users:
            return []
        return self.users[username]

import unittest

class ChatTestAddUser(unittest.TestCase):
    def test_add_user(self):
        chat = Chat()
        self.assertEqual(chat.add_user('John'), True)
        self.assertEqual(chat.users, {'John': []})
    def test_add_user_2(self):
        chat = Chat()
        chat.users = {'John': []}
        self.assertEqual(chat.add_user('John'), False)
        self.assertEqual(chat.users, {'John': []})

    def test_add_user_3(self):
        chat = Chat()
        chat.users = {'John': []}
        self.assertEqual(chat.add_user('Mary'), True)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})

    def test_add_user_4(self):
        chat = Chat()
        chat.users = {'John': []}
        self.assertEqual(chat.add_user('Mary'), True)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})

    def test_add_user_5(self):
        chat = Chat()
        self.assertEqual(chat.add_user('John'), True)
        self.assertEqual(chat.add_user('Mary'), True)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})

class ChatTestRemoveUser(unittest.TestCase):
    def test_remove_user(self):
        chat = Chat()
        chat.users = {'John': []}
        self.assertEqual(chat.remove_user('John'), True)
        self.assertEqual(chat.users, {})
    def test_remove_user_2(self):
        chat = Chat()
        self.assertEqual(chat.remove_user('John'), False)
        self.assertEqual(chat.users, {})

    def test_remove_user_3(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.remove_user('John'), True)
        self.assertEqual(chat.users, {'Mary': []})

    def test_remove_user_4(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.remove_user('Mary'), True)
        self.assertEqual(chat.remove_user('John'), True)
        self.assertEqual(chat.users, {})

    def test_remove_user_5(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.remove_user('Amy'), False)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})

class ChatTestSendMessage(unittest.TestCase):
    def test_send_message(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.assertEqual(chat.send_message('John', 'Mary', 'Hello'), True)
        self.assertEqual(chat.users, {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}], 'Mary': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}]})

    def test_send_message_2(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.send_message('John', 'Tom', 'Hello'), False)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})

    def test_send_message_3(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.send_message('Amy', 'Mary', 'Hello'), False)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})

    def test_send_message_4(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.send_message('Amy', 'Tom', 'Hello'), False)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})

    def test_send_message_5(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.send_message('Amy', 'Amy', 'Hello'), False)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})


class ChatTestGetMessages(unittest.TestCase):
    def test_get_messages(self):
        chat = Chat()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}]}
        self.assertEqual(chat.get_messages('John'), [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}])

    def test_get_messages_2(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.get_messages('John'), [])

    def test_get_messages_3(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.get_messages('Amy'), [])

    def test_get_messages_4(self):
        chat = Chat()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}]}
        self.assertEqual(chat.get_messages('Mary'), [])

    def test_get_messages_5(self):
        chat = Chat()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}]}
        self.assertEqual(chat.get_messages('Amy'), [])

class ChatTestMain(unittest.TestCase):
    def test_main(self):
        chat = Chat()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.assertEqual(chat.add_user('John'), True)
        self.assertEqual(chat.add_user('Mary'), True)
        self.assertEqual(chat.add_user('Amy'), True)
        self.assertEqual(chat.users, {'John': [], 'Mary': [], 'Amy': []})
        self.assertEqual(chat.remove_user('Amy'), True)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})
        self.assertEqual(chat.send_message('John', 'Mary', 'Hello'), True)
        self.assertEqual(chat.send_message('John', 'Tom', 'Hello'), False)
        self.assertEqual(chat.users, {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}], 'Mary': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}]})
        self.assertEqual(chat.get_messages('John'), [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}])
        self.assertEqual(chat.get_messages('Mary'), [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}])

    def test_main_2(self):
        chat = Chat()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.assertEqual(chat.remove_user('Amy'), False)
        self.assertEqual(chat.add_user('John'), True)
        self.assertEqual(chat.add_user('Mary'), True)
        self.assertEqual(chat.add_user('Amy'), True)
        self.assertEqual(chat.users, {'John': [], 'Mary': [], 'Amy': []})
        self.assertEqual(chat.send_message('John', 'Mary', 'Hello'), True)
        self.assertEqual(chat.send_message('John', 'Tom', 'Hello'), False)
        self.assertEqual(chat.remove_user('Amy'), True)
        self.assertEqual(chat.users, {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}], 'Mary': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}]})
        self.assertEqual(chat.users, {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}], 'Mary': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}]})
        self.assertEqual(chat.get_messages('John'), [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}])

if __name__ == '__main__':
    unittest.main()
