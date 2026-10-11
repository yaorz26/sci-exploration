class Server:

    def __init__(self):
        self.white_list = []
        self.send_struct = {}
        self.receive_struct = {}

    def add_white_list(self, addr):
        if addr in self.white_list:
            return False
        else:
            self.white_list.append(addr)
            return self.white_list

    def del_white_list(self, addr):
        if addr not in self.white_list:
            return False
        else:
            self.white_list.remove(addr)
            return self.white_list

    def recv(self, info):
        if not isinstance(info, dict) or "addr" not in info or "content" not in info:
            return -1
        addr = info["addr"]
        content = info["content"]
        if addr not in self.white_list:
            return False
        else:
            self.receive_struct = {"addr": addr, "content": content}
            return self.receive_struct["content"]

    def send(self, info):
        if not isinstance(info, dict) or "addr" not in info or "content" not in info:
            return "info structure is not correct"
        self.send_struct = {"addr": info["addr"], "content": info["content"]}

    def show(self, type):
        if type == "send":
            return self.send_struct
        elif type == "receive":
            return self.receive_struct
        else:
            return False

import unittest

class ServerTestAddWhiteList(unittest.TestCase):
    def test_add_white_list_1(self):
        server = Server()
        server.add_white_list(88)
        self.assertEqual(server.white_list, [88])

    def test_add_white_list_2(self):
        server = Server()
        server.add_white_list(88)
        self.assertEqual(server.add_white_list(88), False)

    def test_add_white_list_3(self):
        server = Server()
        server.add_white_list(88)
        server.add_white_list(11)
        self.assertEqual(server.add_white_list(11), False)

    def test_add_white_list_4(self):
        server = Server()
        server.add_white_list(11)
        self.assertEqual(server.white_list, [11])

    def test_add_white_list_5(self):
        server = Server()
        server.add_white_list(88)
        server.add_white_list(11)
        server.add_white_list(22)
        self.assertEqual(server.add_white_list(22), False)


class ServerTestDelWhiteList(unittest.TestCase):
    def test_del_white_list_1(self):
        server = Server()
        server.add_white_list(88)
        server.del_white_list(88)
        self.assertEqual(server.white_list, [])

    def test_del_white_list_2(self):
        server = Server()
        self.assertEqual(server.del_white_list(88), False)

    def test_del_white_list_3(self):
        server = Server()
        self.assertEqual(server.del_white_list(11), False)

    def test_del_white_list_4(self):
        server = Server()
        self.assertEqual(server.del_white_list(22), False)

    def test_del_white_list_5(self):
        server = Server()
        server.add_white_list(11)
        self.assertEqual(server.del_white_list(22), False)


class ServerTestRecv(unittest.TestCase):
    def test_recv_1(self):
        server = Server()
        server.add_white_list(88)
        server.recv({"addr": 88, "content": "abc"})
        self.assertEqual(server.receive_struct, {"addr": 88, "content": "abc"})

    def test_recv_2(self):
        server = Server()
        server.add_white_list(88)
        flag = server.recv({"addr": 66, "content": "abc"})
        self.assertEqual(server.receive_struct, {})
        self.assertEqual(flag, False)

    def test_recv_3(self):
        server = Server()
        flag = server.recv([88])
        self.assertEqual(server.receive_struct, {})
        self.assertEqual(flag, -1)

    def test_recv_4(self):
        server = Server()
        flag = server.recv({"addr": 88})
        self.assertEqual(server.receive_struct, {})
        self.assertEqual(flag, -1)

    def test_recv_5(self):
        server = Server()
        flag = server.recv({"content": "abc"})
        self.assertEqual(server.receive_struct, {})
        self.assertEqual(flag, -1)

import unittest

class ServerTestSend(unittest.TestCase):
    def test_send_1(self):
        server = Server()
        server.send({"addr": 88, "content": "abc"})
        self.assertEqual(server.send_struct, {"addr": 88, "content": "abc"})

    def test_send_2(self):
        server = Server()
        flag = server.send({"addr": 88})
        self.assertEqual(flag, "info structure is not correct")

    def test_send_3(self):
        server = Server()
        flag = server.send({"content": "abc"})
        self.assertEqual(flag, "info structure is not correct")

    def test_send_4(self):
        server = Server()
        flag = server.send([])
        self.assertEqual(flag, "info structure is not correct")

    def test_send_5(self):
        server = Server()
        server.send({"addr": 66, "content": "abc"})
        self.assertEqual(server.send_struct, {"addr": 66, "content": "abc"})


class ServerTestShow(unittest.TestCase):
    def test_show_1(self):
        server = Server()
        server.add_white_list(66)
        server.send({"addr": 88, "content": "abc"})
        server.recv({"addr": 66, "content": "ABC"})
        self.assertEqual(server.show("send"), {"addr": 88, "content": "abc"})

    def test_show_2(self):
        server = Server()
        server.add_white_list(66)
        server.send({"addr": 88, "content": "abc"})
        server.recv({"addr": 66, "content": "ABC"})
        self.assertEqual(server.show("receive"), {"addr": 66, "content": "ABC"})

    def test_show_3(self):
        server = Server()
        server.add_white_list(66)
        server.send({"addr": 88, "content": "abc"})
        server.recv({"addr": 66, "content": "ABC"})
        self.assertEqual(server.show("abcdefg"), False)

    def test_show_4(self):
        server = Server()
        server.add_white_list(66)
        server.send({"addr": 11, "content": "abc"})
        server.recv({"addr": 66, "content": "ABC"})
        self.assertEqual(server.show("send"), {"addr": 11, "content": "abc"})

    def test_show_5(self):
        server = Server()
        server.add_white_list(66)
        server.send({"addr": 22, "content": "abc"})
        server.recv({"addr": 66, "content": "ABC"})
        self.assertEqual(server.show("send"), {"addr": 22, "content": "abc"})


class ServerTest(unittest.TestCase):
    def test_server(self):
        server = Server()
        server.add_white_list(88)
        self.assertEqual(server.white_list, [88])
        server.del_white_list(88)
        self.assertEqual(server.white_list, [])
        server.add_white_list(88)
        server.recv({"addr": 88, "content": "abc"})
        self.assertEqual(server.receive_struct, {"addr": 88, "content": "abc"})
        server.send({"addr": 66, "content": "ABC"})
        self.assertEqual(server.send_struct, {"addr": 66, "content": "ABC"})
        server.recv({"addr": 88, "content": "abc"})
        self.assertEqual(server.show("receive"), {"addr": 88, "content": "abc"})

if __name__ == '__main__':
    unittest.main()
