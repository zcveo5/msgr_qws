import json
import socket
import threading
import time
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
        self._codec = crypt.generate_salt()
        print('[*] codec created')
        self.sock.connect(self.ip)
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

    def communicate(self, send, limit=1024):
        """Request - Response system"""
        ans = None
        def wrp(_s, _l):
            nonlocal ans
            self.send(_s)
            ans = self.recv(_l)
        com_th = threading.Thread(target=wrp, args=(send, limit))
        com_th.start()
        time.sleep(2)
        if ans is None:
            print('[*] timed out')
            def join_w():
                com_th.join()
                print('[*] thread closed')
            threading.Thread(target=join_w).start()
            return None
        else:
            print('[*] completed')
            return ans
