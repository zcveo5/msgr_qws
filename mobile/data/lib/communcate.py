import json
import socket
from json import JSONDecodeError

import data.lib.crypt as crypt


class Server:
    def __init__(self, host, port, username, password):
        self.ip = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.usr = username
        self.passw = password

        self.username = username
        self.password = password

        self._codec = None

    def connect(self):
        self.sock.connect(self.ip)
        self._codec = crypt.generate_salt()
        self.sock.send(f'ConnectionKey$:${self._codec}'.encode('utf-8'))
        self.send({'username': self.usr, 'password': self.passw, 'type': 'auth'})

    def send(self, d):
        self.sock.send(str(crypt.encrypt(f'{d}', self._codec)).encode('utf-8'))

    def recv(self, limit=1024):
        _no_dct = crypt.decrypt(self.sock.recv(limit).decode('utf-8'), self._codec).replace("'", '"')
        try:
            return json.loads(_no_dct)
        except JSONDecodeError:
            return _no_dct
