import unittest
import socket
import os
import sys
import hashlib

# Dynamically append root project directory to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, "Client"))
sys.path.insert(0, os.path.join(project_root, "Server"))

from Client import EMessageClient
from Server import EMessageServer
from config import server_hashed_password


class TestEMessageClient(unittest.TestCase):
    def setUp(self):
        self.client = EMessageClient()

    def tearDown(self):
        if self.client.socket:
            self.client.socket.close()

    def test_client_initialization(self):
        self.assertIsInstance(self.client.socket, socket.socket)

    def test_client_connection_failure(self):
        self.client.socket.settimeout(1)
        with self.assertRaises(Exception):
            self.client.socket.connect(("localhost", 9999))


class TestEMessageServer(unittest.TestCase):
    def setUp(self):
        self.server = EMessageServer()
        EMessageServer.username_list = []
        self.server.clients_list = []

    def tearDown(self):
        if self.server.socket:
            self.server.socket.close()

    def test_server_initialization(self):
        self.assertIsInstance(self.server.socket, socket.socket)
        self.assertEqual(self.server.clients_list, [])
        self.assertEqual(self.server.username_list, [])

    def test_password_verification(self):
        correct_password = b"123"
        valid = self.server.verify("testuser", correct_password)
        self.assertTrue(valid)

        self.assertFalse(self.server.verify("testuser!", correct_password))
        self.server.username_list.append("testuser")
        self.assertFalse(self.server.verify("testuser", correct_password))


if __name__ == '__main__':
    unittest.main()
