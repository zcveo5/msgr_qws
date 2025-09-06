import json
import socket
import threading
import time
from json import JSONDecodeError
import data.lib.crypt as crypt


class Server:
    """вспомогательный класс для сообщения между сервером и клиентом"""
    def __init__(self, host, port, username, password):
        self.ip = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.usr = username
        self.passw = password

        self.username = username
        self.password = password

        self._codec = None # ключ шифрования (модуль crypt)
        self.req_id = 0  # Счетчик идентификаторов запросов
        self._lock = threading.Lock()  # Блокировка для безопасного увеличения счетчика

        self._unk_req = {}

    def connect(self, adds=None):
        """Подключение к серверу"""
        self._codec = crypt.generate_salt()
        print('[*] codec created')
        self.sock.connect(self.ip)
        self.sock.send(f'ConnectionKey$:${self._codec}'.encode('utf-8'))
        auth_req = {'username': self.usr, 'password': self.passw, 'type': 'auth'}

        login_result = self.communicate(auth_req) # отправляет запрос на логин
        if login_result['status'] != 'ok':
            raise Exception('Login failed')
        print(login_result)

    def send(self, d):
        """шифрует и отправляет запрос"""
        self.sock.send(str(crypt.encrypt(f'{d}', self._codec)).encode('utf-8'))

    def recv(self, limit=1024) -> dict | str:
        """расшифровывает ответ сервера и пытается конверторовать в словарь"""
        _no_dct = crypt.decrypt(self.sock.recv(limit).decode('utf-8'), self._codec)
        try:
            return json.loads(_no_dct)
        except JSONDecodeError:
            return _no_dct

    def communicate(self, send_data, limit=1024, waiting_actions: () = None) -> dict | None:
        """система запрос - ответ с использованием ID запросов"""
        with self._lock:
            current_id = self.req_id
            self.req_id += 1

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
            print(f'[ServerCom][{current_id}] started wrp')
            print(f'[ServerCom][{current_id}] sending {_s}')
            self.send(_s)
            while ans is None:
                if bad_ans_c > 10:
                    break
                try:
                    response = self.recv(_l)
                    print(f'[ServerCom][{current_id}] received {response}')
                    # Проверяем, что ответ содержит правильный ID
                    if isinstance(response, str):
                        response = {'msg': response}
                    if isinstance(response, dict) and response.get('req_id') == current_id:
                        print(f'[ServerCom][{current_id}] our answer is: {response}')
                        ans = response
                        break
                    else:
                        # Сохраняем ответы с другими ID для возможного использования в будущем
                        other_id = response.get('req_id', -1)
                        self._unk_req[other_id] = response
                        bad_ans_c += 1

                        # Проверяем, нет ли ответа на наш запрос среди сохраненных
                        if current_id in self._unk_req:
                            ans = self._unk_req.pop(current_id)
                            break
                except Exception as _send_ex:
                    exc = _send_ex
                    break

        com_th = threading.Thread(target=wrp, args=(send_data_with_id, limit), daemon=True)
        com_th.start()
        timeout = 0
        while ans is None:
            time.sleep(0.01)
            if waiting_actions is not None:
                if isinstance(waiting_actions, tuple):
                    for action in waiting_actions:
                        action()
                elif callable(waiting_actions):
                    waiting_actions()
            timeout += 0.01
            if timeout >= 5.0:
                break
        if ans is None:
            print('[*] timed out')

            def join_w():
                com_th.join(timeout=1.0)
                print('[*] thread closed')

            threading.Thread(target=join_w, daemon=True).start()
        print('[*] completed')
        if exc is not None:
            raise exc
        return ans

    def get_unknown_request(self, req_id):
        """Получить сохраненный ответ по ID запроса"""
        return self._unk_req.pop(req_id, None)

    def recv_split_request(self, start_req):
        buffer = []
        self.send(start_req)
        while '!!$%&END' not in buffer:
            part = self.recv()
            print(f'[ssr {start_req}] {part}')
            part = part['h']
            if part is None:
                break
            buffer.append(part)
        string_buffer = ''
        for _i in buffer[0:-1]:
            string_buffer += str(_i)
        string_buffer = string_buffer.replace("'", '"').replace("False", 'false').replace("True", 'true')
        print(f'[ssr {start_req}] result {string_buffer}')
        try:
            return json.loads(string_buffer)
        except JSONDecodeError:
            return {}
