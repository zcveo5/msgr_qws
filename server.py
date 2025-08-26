import json
import os.path
import socket
import sys
import threading
import time
from json import JSONDecodeError

import data.lib.crypt as crypt

clients = {}
if not os.path.exists('./data.json'):
    with open('./data.json', 'w') as fl:
        fl.write('{}')

data = json.load(open('./data.json', 'r'))

class Client:
    def __init__(self, _sock: socket.socket):
        self.sock = _sock
        self.addr = self.sock.getpeername()
        self.alive = True
        self.fprint = lambda s: print(f'[{self.addr}] {s}')
        self.fprint(f'init {self.addr}')
        threading.Thread(target=self.handle).start()

    def handle(self):
        self.fprint('handle launched')
        last = ''
        repeat_count = 0
        while self.alive:
            if not self.alive:
                break
            if repeat_count > 5:
                self.fprint('too much repeating requests, closing')
                break
            try:
                msg = self.sock.recv(4096).decode('utf-8')
            except ConnectionError:
                break
            ans = {}

            if self.addr in clients:
                msg_decoded = crypt.decrypt(msg, clients[self.addr]['key']).replace("'", '"').replace('False', 'false').replace('True', 'true')
                try:
                    self.fprint(msg_decoded)
                    dct = json.loads(msg_decoded)
                except JSONDecodeError:
                    self.fprint(f'corrupted req: {msg_decoded}')
                if dct['type'] == 'auth':
                    if dct['username'] not in data:
                        data.update({dct['username']: {'password': dct['password'], 'queue': [], 'chat_history': {}}})
                    else:
                        if dct['password'] == data[dct['username']]['password']:
                            ans = {'type': 'login', 'status': 'ok'}
                            clients[self.addr]['username'] = dct['username']
                            clients[self.addr]['password'] = dct['password']
                        else:
                            ans = {'type': 'login', 'status': 'fail'}
                            self.alive = False
                elif dct['type'] == 'msg':
                    to_cl = dct['to'].split('/')
                    if to_cl[0] == 'public':
                        for i in clients.values():
                            if i['username'] != dct['from']:
                                i['class'].sock.send(f'{crypt.encrypt(f'{dct}', i["key"])}'.encode('utf-8'))
                    else:
                        if to_cl[1] not in clients and to_cl[1] in data:
                            data[to_cl[1]]['queue'].append(dct)
                        elif to_cl[1] in clients:
                            for i in clients.values():
                                if i['username'] == to_cl[1]:
                                    i['class'].sock.send(f'{crypt.encrypt(f'{dct}', i["key"])}'.encode('utf-8'))
                elif dct['type'] == 'get_chat_history':
                    byte_data = str(data[clients[self.addr]['username']]['chat_history']).encode('utf-8')
                    chunk_size = 1024
                    chunks = [
                        byte_data[i:i + chunk_size]
                        for i in range(0, len(byte_data), chunk_size)
                    ]
                    for chunk in chunks:
                        decoded_chunk = chunk.decode('utf-8', errors='replace')
                        self.sock.send(f'{crypt.encrypt("{'type': 'chat_hist_part', 'answer': " + decoded_chunk + '}', clients[self.addr]["key"])}'.encode('utf-8'))

            if 'ConnectionKey$:$' in msg:
                self.fprint(f'received connection key for {self.addr}')
                clients.update({self.addr: {'username': '', 'password': '', 'key': ''.join(msg.split('$:$')[1::]), 'class': self}})
            if ans != {}:
                self.sock.send(f'{crypt.encrypt(f'{ans}', clients[self.addr]["key"])}'.encode('utf-8'))

            if msg == '':
                self.fprint('closing')
                break
            if last == msg:
                repeat_count += 1
            last = msg
        clients.pop(self.addr)
        self.fprint('Closed')
        return None



def data_save():
    while True:
        if data != json.load(open('./data.json', 'r')):
            print('[sdm] saving data')
            json.dump(data, open('./data.json', 'w'))
        time.sleep(0.5)


#sys.excepthook = lambda x, y=None, z=None: print(f'tb: {x}, {y}, {z}')
#threading.excepthook = sys.excepthook
print(r'\ MSGR QWS Server /')
print('Staring server...')
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('127.0.0.1', 5252))
listen = 10
server.listen(listen)
print('SERVER INFO:')
print(f'{server.getsockname()[0]}:{server.getsockname()[1]}')
print(f'Listening max {listen} clients')
print('=====')
def accept_wrp():
    while True:
        sock, addr = server.accept()
        print(f'[srv_root] accepted {addr}')
        Client(sock)
threading.Thread(target=accept_wrp, daemon=True).start()
threading.Thread(target=data_save, daemon=True).start()
cm = ''
while cm != 'exit':
    cm = input()
    exec(cm, globals(), locals())