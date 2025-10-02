import json
import random
import socket
import sys
import threading
import time
from json import JSONDecodeError
import data.lib.crypt as crypt
from data.lib.printlib import print_adv, find_h

sock_log = sys.stdout

def refresh_log():
    global sock_log
    sock_log = find_h('Socket')

class Server:
    """вспомогательный класс для сообщения между сервером и клиентом"""
    def __init__(self, host, port, username, password, default_waiting_actions, show_error, use_rr_mode=True):
        if default_waiting_actions is not tuple:
            default_waiting_actions = (default_waiting_actions,)
        self.ip = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.dwa = default_waiting_actions
        self._request_response_mode = use_rr_mode
        self._show_error = show_error

        self.usr = username
        self.passw = password

        self.username = username
        self.password = password

        self._codec = None # ключ шифрования (модуль crypt)
        self.req_id = 0  # Счетчик идентификаторов запросов
        self._lock = threading.Lock()  # Блокировка для безопасного увеличения счетчика

        self._unk_req = {}

    def recreate_sock(self):
        self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, adds=None):
        """Подключение к серверу"""
        self._codec = crypt.generate_salt()
        print_adv('[*] codec created', h=sock_log)
        self.sock.connect(self.ip)
        self.sock.send(f'ConnectionKey$:${self._codec}'.encode('utf-8'))
        if not self._request_response_mode:
            threading.Thread(target=self.async_recv, daemon=True, name=f'AsyncReceive:{self.ip}').start()


    def auth(self):
        auth_req = {'username': self.usr, 'password': self.passw, 'type': 'auth'}

        login_result = self.communicate(auth_req) # отправляет запрос на логин
        if login_result is None or login_result['status'] != 'ok':
            raise Exception('Login failed')
        print_adv(f'Login result: {login_result}', h=sock_log)

    def async_recv(self, limit=1024):
        while True:
            try:
                _response = self._recv(limit=limit)
                print_adv(f'[async-recv] recv {_response}', h=sock_log)
                if _response['req_id'] == 'ServerSideErrorDetails':
                    self._show_error(_response['err'])
                if 'req_id' in _response:
                    self._unk_req[_response['req_id']] = _response
                else:
                    print_adv(f'[async-recv] invalid response: {_response}', h=sock_log)
            except OSError:
                pass
            except Exception as e:
                print_adv(f'[sERR_Wrp-{sock_log.name}][async-recv] {e.__class__.__name__}: {e}', h=sys.stderr)

    def send(self, d):
        """шифрует и отправляет запрос"""
        self.sock.send(str(crypt.encrypt(f'{d}', self._codec)).encode('utf-8'))

    def _recv(self, limit=1024) -> dict | str:
        """расшифровывает ответ сервера и пытается конвертировать в словарь"""
        _no_dct = crypt.decrypt(self.sock.recv(limit).decode('utf-8'), self._codec)
        try:
            return json.loads(_no_dct)
        except JSONDecodeError:
            return _no_dct


    def communicate(self, send_data, limit=1024, waiting_action=None) -> dict | None:
        """система запрос - ответ с использованием ID запросов"""
        with self._lock:
            current_id = self.req_id
            self.req_id = random.randint(0000000000, 9999999999)

        if not callable(waiting_action):
            print_adv(f'[sERR_Wrp-{sock_log.name}][ServerCom{current_id}] waiting_action not callable', h=sys.stderr)

        # Добавляем ID к данным запроса
        if isinstance(send_data, dict):
            send_data_with_id = send_data.copy()
            send_data_with_id['req_id'] = current_id
        else:
            send_data_with_id = {'req_id': current_id, 'msg': send_data}

        ans = None
        exc = None

        def wrp(_s, _l):
            nonlocal ans, exc
            bad_ans_c = 0
            print_adv(f'[ServerCom{current_id}] started wrp', h=sock_log)
            print_adv(f'[ServerCom{current_id}] sending {_s}', h=sock_log)

            self.send(_s)

            while ans is None:
                if bad_ans_c > 10:
                    break
                try:
                    if current_id in self._unk_req:
                        print_adv(f'[ServerCom{current_id}] breaking ans while: answer found in _unk_req', h=sock_log)
                        ans = self._unk_req.pop(current_id)
                        break

                    if self._request_response_mode:
                        response = self._recv(_l)
                        print_adv(f'[ServerCom{current_id}] received {response}', h=sock_log)
                        if isinstance(response, str):
                            response = {'msg': response}
                        if isinstance(response, dict) and response.get('req_id') == current_id:
                            print_adv(f'[ServerCom{current_id}] our answer is: {response}', h=sock_log)
                            ans = response
                            break
                        else:
                            other_id = response.get('req_id', -1)
                            self._unk_req[other_id] = response
                            bad_ans_c += 1
                except Exception as _send_ex:
                    exc = _send_ex
                    break

        com_th = threading.Thread(target=wrp, args=(send_data_with_id, limit), daemon=True)
        com_th.start()
        timeout = 0
        while ans is None:
            try:
                time.sleep(0.01)
            except KeyboardInterrupt:
                print_adv(f'[sERR_Wrp-{sock_log.name}][ServerCom{current_id}] KeyboardInterrupt at waiting response',
                          h=sys.stderr)
            if waiting_action is not None and callable(waiting_action):
                waiting_action()
            for i in self.dwa:
                if callable(i):
                    i()
                else:
                    print_adv(f'[sERR_Wrp-{sock_log.name}][ServerCom{current_id}] {i} waiting action not callable', h=sys.stderr)
            timeout += 0.01
            if timeout >= 5.0:
                break
        if ans is None:
            print_adv('[*] timed out')

            def join_w():
                com_th.join(timeout=1.0)
                print_adv(f'[ServerCom{current_id}][*] thread closed', h=sock_log)

            threading.Thread(target=join_w, daemon=True).start()
        print_adv(f'[ServerCom{current_id}][*] completed', h=sock_log)
        if exc is not None:
            raise exc
        return ans

    def get_unknown_request(self, req_id):
        """Получить сохраненный ответ по ID запроса"""
        a = None
        while a is None:
            a = self._unk_req.pop(req_id, None)
        return a

    def recv_split_request(self, start_req):
        with self._lock:
            current_id = self.req_id
            self.req_id = random.randint(1000000000, 9999999999)
        buffer = []
        start_req.update({'req_id': current_id})
        self.send(start_req)
        while '!!$%&END' not in buffer:
            for i in self.dwa:
                if not callable(i):
                    print_adv(f'[sERR-Wrp-{sock_log.name}][ssr {start_req['type']}] w_a {i} not callable', h=sys.stderr)
                else:
                    i()
            if self._request_response_mode:
                part = self._recv()
            else:
                part = self.get_unknown_request(current_id)
            print_adv(f'[ssr {start_req["type"]}] {part}', h=sock_log)
            part = part['h']
            if part is None:
                break
            buffer.append(part)
            current_id += 1
        string_buffer = ''
        for _i in buffer[0:-1]:
            string_buffer += str(_i)
        string_buffer = string_buffer.replace("'", '"').replace("False", 'false').replace("True", 'true')
        print_adv(f'[ssr {start_req["type"]}] result {string_buffer}', h=sock_log)
        try:
            return json.loads(string_buffer)
        except JSONDecodeError:
            return {}
