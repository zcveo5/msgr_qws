import json
import math
import os.path
import random
import socket
import threading
import time
import traceback
from json import JSONDecodeError

import data.lib.crypt as crypt

clients = {}
if not os.path.exists('./data.json'):
    with open('./data.json', 'w') as fl:
        fl.write('{"users": {}, "chats": {}}')

data = json.load(open('./data.json', 'r'))

class Client:
    def __init__(self, _sock: socket.socket):
        self.sock = _sock
        self.addr = self.sock.getpeername()
        self.alive = True
        self.fprint = lambda s: print(f'[{self.addr}] {s}')
        self.fprint(f'init {self.addr}')
        self._chat_hist = {}
        def wrapper():
            try:
                self.handle()
            except Exception as _handle_exception:
                self.send({'type': 'show_server_error', 'err': f'Error handling your client: {''.join(traceback.format_exception(_handle_exception))[100:]}', 'req_id': 'ServerSideErrorDetails'})
                self.fprint(f'Closing. Caused by: {_handle_exception.__class__}:{_handle_exception}\nTraceback:\n{''.join(traceback.format_exception(_handle_exception))}')
        threading.Thread(target=wrapper, name=f'Client:{self.addr[0]}:{self.addr[1]}').start()

    def handle(self):
        self.fprint('handle launched')
        last = ''
        repeat_count = 0
        while self.alive:
            if not self.alive:
                break
            try:
                msg = self.sock.recv(4096).decode('utf-8')
            except ConnectionError:
                msg = ''
                break
            ans = {}

            if self.addr in clients:
                try:
                    msg_decoded = crypt.decrypt(msg, clients[self.addr]['key']).replace("'", '"').replace('False', 'false').replace('True', 'true')
                except SyntaxError:
                    self.alive = False
                    msg_decoded = {}
                try:
                    self.fprint(msg_decoded)
                    dct = json.loads(msg_decoded)
                except JSONDecodeError:
                    self.fprint(f'corrupted req: {msg_decoded}')
                if dct['type'] == 'auth':
                    if dct['username'] not in data['users'] and len(dct['username']) > 3 and ' ' not in dct['username']:
                        data['users'].update({dct['username']: {'password': dct['password'], 'queue': [], 'chat_history': {}, 'contacts': []}})
                        clients[self.addr]['username'] = dct['username']
                        clients[self.addr]['password'] = dct['password']
                    else:
                        if dct['password'] == data['users'][dct['username']]['password']:
                            ans = {'type': 'login', 'status': 'ok'}
                            clients[self.addr]['username'] = dct['username']
                            clients[self.addr]['password'] = dct['password']
                        else:
                            ans = {'type': 'login', 'status': 'fail'}
                            self.alive = False
                elif dct['type'] == 'msg':
                    if dct['from'] in data['chats'][dct['to_cl']]['users']:
                        for _user in data['chats'][dct['to_cl']]['users']:
                            if _user != dct['from']:
                                dct_copy = dct.copy()
                                dct_copy.pop('req_id')
                                data['users'][_user]['queue'].append(dct_copy)
                                print(dct, _user)
                        dct_copy = dct.copy()
                        dct_copy.pop('req_id')
                        dct_copy.pop('type')
                        dct_copy.pop('to_cl')
                        data['chats'][dct['to_cl']]['msgs'].append(dct_copy)
                        ans = {'status': 'Sent'}
                elif dct['type'] == 'create_chat':
                    chat_cfg = {'users': [clients[self.addr]['username']] + dct['users'], 'name': dct['name'], 'msgs': [], 'is_public': dct['is_public'], 'admins': [clients[self.addr]['username']]}
                    link = ''
                    if dct['is_public']:
                        if dct['public_id'] not in data['chats']:
                            chat_cfg.update({'link': dct['public_id']})
                            link = dct['public_id']
                    else:
                        symb = "A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z. B, C, D, F, G, H, J, K, L, M, N, P, Q, R, S, T, V, W, X, Y, Z, ., +, -, =, _".split(', ')
                        random.shuffle(symb)
                        link = ''
                        ints = random.randint(1000000, 9999999)
                        for i in range(0, 15):
                            if i % 2 == 0:
                                link += str(ints)[random.randint(0, 6)]
                            else:
                                _e = symb[random.randint(0, len(symb) - 1)]
                                if random.randint(0, 1) == 1:
                                    link += _e.lower()
                                else:
                                    link += _e
                        chat_cfg.update({'link': link})
                    data['chats'][link] = chat_cfg
                    print(link)
                    for _user in data['chats'][link]['users']:
                        _inf = data['chats'][link]
                        _inf['type'] = 'new_chat'
                        data['users'][_user]['queue'].append(_inf)
                    ans = data['chats'][link]
                elif dct['type'] == 'queue_get':
                    ans = {'q': data['users'][clients[self.addr]['username']]['queue'].copy()}
                    data['users'][clients[self.addr]['username']]['queue'] = []
                elif dct['type'] == 'get_contacts':
                    data['users'][clients[self.addr]['username']]['contacts'] = list(set(data['users'][clients[self.addr]['username']]['contacts']))
                    ans = {'c': data['users'][clients[self.addr]['username']]['contacts']}
                elif dct['type'] == 'get_chat_hist':
                    for _n, _i in data['chats'].items():
                        if clients[self.addr]['username'] in _i['users']:
                            data['users'][clients[self.addr]['username']]['chat_history'][_i['name']] = _i.copy()
                        if clients[self.addr]['username'] not in _i['users'] and _i['name'] in data['users'][clients[self.addr]['username']]['chat_history']:
                            data['users'][clients[self.addr]['username']]['chat_history'].pop(_i['name'])
                    self._chat_hist = data['users'][clients[self.addr]['username']]['chat_history'].copy()
                    hist_raw = repr(data['users'][clients[self.addr]['username']]['chat_history'])
                    chat_hist_part_size = 500
                    self.fprint(f'[chat hist] sending chat hist - len {len(hist_raw)} - parts {math.ceil(len(hist_raw) / chat_hist_part_size)} (not ceiled parts {(len(hist_raw) / chat_hist_part_size)})')
                    ind = 0
                    plus_req_id = 0
                    for _i in range(0, math.ceil(len(hist_raw) / chat_hist_part_size)):
                        part = str(hist_raw[ind:ind + chat_hist_part_size]).replace('"', "'")
                        self.fprint(f'[chat hist] sending chat hist part {_i} #{part}#')
                        final_req = {'h': f'{part}', 'req_id': dct['req_id'] + plus_req_id}
                        self.fprint(f'[chat hist] checking part valid: str - {len(repr(final_req))}/{chat_hist_part_size}, bytes - {len(repr(final_req).encode('utf-8'))}/{chat_hist_part_size}')
                        self.send(final_req)
                        plus_req_id += 1
                        ind += chat_hist_part_size
                        time.sleep(0.5)
                    self.send({'h': '!!$%&END', 'req_id': dct['req_id'] + plus_req_id})
                elif dct['type'] == 'be_ready_for_chat_hist':
                    buffer = []
                    while '!!$%&END' not in buffer:
                        part = self.recv(1024)
                        if part == '':
                            break
                        self.fprint(f'[chat hist] {part}')
                        buffer.append(part)
                    self.fprint(buffer)
                    string_buffer = json.loads(''.join(buffer[0:-1]).replace("'", '"').replace("False", 'false').replace("True", 'true'))
                    data['users'][clients[self.addr]['username']]['chat_history'] = string_buffer
                elif dct['type'] == 'get_public_chats_all':
                    hist_raw = []
                    for i in data['users']:
                        hist_raw.append(i)
                    for i in data['chats'].values():
                        if i['is_public']:
                            hist_raw.append(i)
                    hist_raw = str({'h': hist_raw})
                    ind = 0
                    plus_req_id = 0
                    for i in range(0, math.ceil(len(hist_raw) / 1002)):
                        part = str(hist_raw[ind:ind + 1002]).replace('"', "'")
                        self.fprint(f'#{part}#')
                        self.send({'h': f'{part}', 'req_id': dct['req_id'] + plus_req_id})
                        plus_req_id += 1
                        ind += 1002
                        time.sleep(0.5)
                    self.send({'h': '!!$%&END', 'req_id': dct['req_id'] + plus_req_id})
                elif dct['type'] == 'add_to_contacts':
                    if dct['u'] not in data['users'][clients[self.addr]['username']]['contacts']:
                        data['users'][clients[self.addr]['username']]['contacts'].append(dct['u'])
                elif dct['type'] == 'join':
                    data['chats'][dct['u']]['users'].append(clients[self.addr]['username'])
                elif dct['type'] == 'chat_manage_get_my_actions':
                    if clients[self.addr]['username'] in data['chats'][dct['chat']]['admins']:
                        ans = {'a': ['manage_users', 'create_admin', 'delete_admin', 'invite_users']}
                    else:
                        ans = {'a': ['invite_users']}
                elif dct['type'] == 'add_users':
                    for _u in dct['c']:
                        if _u not in data['chats'][dct['chat']]['users']:
                            data['chats'][dct['chat']]['users'].append(_u)
                elif dct['type'] == 'delete_user':
                    if clients[self.addr]['username'] in data['chats'][dct['chat']]['admins']:
                        data['chats'][dct['chat']]['users'].remove(dct['delete_user'])
                elif dct['type'] == 'add_admin':
                    if clients[self.addr]['username'] in data['chats'][dct['chat']]['admins']:
                        data['chats'][dct['chat']]['admins'].append(dct['add_admin'])
                elif dct['type'] == 'remove_admin':
                    if clients[self.addr]['username'] in data['chats'][dct['chat']]['admins'] and dct['remove_admin'] != data['chats'][dct['chat']]['admins'][0]:
                        data['chats'][dct['chat']]['admins'].remove(dct['remove_admin'])
                elif dct['type'] == 'get_plugin_list':

                    ans = {'status': 'ok', 'l': []}


                if self._chat_hist != data['users'][clients[self.addr]['username']]['chat_history']:
                    if 'force_chat_hist_update' not in data['users'][clients[self.addr]['username']]['queue']:
                        data['users'][clients[self.addr]['username']]['queue'].append({'type': 'force_chat_hist_update'})
                self.fprint(f'is chat hist actual: {self._chat_hist == data['users'][clients[self.addr]['username']]['chat_history']}')
            if 'ConnectionKey$:$' in msg:
                self.fprint(f'received connection key for {self.addr}')
                clients.update({self.addr: {'username': '', 'password': '', 'key': ''.join(msg.split('$:$')[1::]), 'class': self}})
            if ans != {}:
                if 'req_id' in dct:
                    ans['req_id'] = dct['req_id']
                self.send(ans)

            if msg == '':
                self.fprint('closing')
                break
            if last == msg:
                repeat_count += 1
            last = msg
        try:
            clients.pop(self.addr)
        except KeyError:
            self.fprint('no such client')
        self.fprint('Closed')
        return None

    def send(self, _s):
        self.fprint(f'sending #{_s}#')
        if isinstance(_s, dict):
            _s = json.dumps(_s)
        self.sock.send(f'{crypt.encrypt(_s, clients[self.addr]["key"])}'.encode('utf-8'))

    def recv(self, _l):
        return crypt.decrypt(self.sock.recv(_l).decode('utf-8'), clients[self.addr]['key'])



def data_save():
    while True:
        if data != json.load(open('./data.json', 'r')):
            print('[sdm] saving data')
            json.dump(data, open('./data.json', 'w'), indent=4)
        time.sleep(0.1)


def data_optimize():
    global data
    while True:
        data_copy = data.copy()
        for _chat in data['chats']:
            data_copy['chats'][_chat]['users'] = list(set(data_copy['chats'][_chat]['users']))
        if data != data_copy:
            print('[odm] optimizing data')
            data = data_copy
        time.sleep(10)


def clone_plugins():
    print('cloning plugins...')


#sys.excepthook = lambda x, y=None, z=None: print(f'tb: {x}, {y}, {z}')
#threading.excepthook = sys.excepthook
print(r' - \ MSGR QWS Server / - ')
print('Checking data valid...')
chat_cfg_template = {'users': [], 'name': f'TemplateName{random.randint(1230000, 123123143)}', 'msgs': [], 'is_public': False, 'admins': [], 'link': f'ah93uwhg4r9auvb0-awa9hnw{random.randint(17348175, 18724589190)}'}
for chat in data['chats'].values():
    for need_key in chat_cfg_template:
        if need_key not in chat:
            chat[need_key] = chat_cfg_template[need_key]


print('Staring server...')
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('127.0.0.1', 5252))
listen = 10
server.listen(listen)
print('SERVER INFO:')
print(f'{server.getsockname()[0]}:{server.getsockname()[1]}')
print(f'Listening max {listen} clients')
print('=====')
if 'chats' not in data:
    data['chats'] = {}
if 'users' not in data:
    data['users'] = {}
def accept_wrp():
    while True:
        sock, addr = server.accept()
        print(f'[srv_root] accepted {addr}')
        Client(sock)
threading.Thread(target=accept_wrp, daemon=True).start()
threading.Thread(target=data_save, daemon=True).start()
threading.Thread(target=data_optimize, daemon=True).start()
threading.Thread(target=clone_plugins, daemon=True).start()
cm = ''
while cm != 'exit':
    cm = input()
    try:
        exec(cm, globals(), locals())
    except Exception as _cmd_ex:
        print(_cmd_ex)
else:
    print('[sdm] saving data')
    json.dump(data, open('./data.json', 'w'), indent=4)
    print('[srv_root] closing connection with clients...')
    for i in threading.enumerate():
        if 'Client:' in i.name:
            print(f'[srv_root] {i.name} {" "*50}', end='\r')
            i.join(0.5)
    print('[srv_root] closing another threads...')
    for i in threading.enumerate():
        if i != threading.main_thread():
            print(f'[srv_root] closed {i}')
            i.join(0.5)
