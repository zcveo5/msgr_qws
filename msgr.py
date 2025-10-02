import importlib
import sys
from tkinter.messagebox import showerror
from data.lib.printlib import print_adv

for _module in ['ctypes', 'tkinter', 'requests', 'data.lib.utils', 'data.lib.communicate', 'data.lib.printlib']:
    try:
        exec(f'import {_module}')
    except Exception as _ex:
        input(f"MSGR-QWS Required modules is not installed. Please install {_module} (Caused by {_ex.__class__}: {_ex})")
        exit()

import ctypes
import json
import math
import os
import platform
import signal
import time
import traceback
import requests
import data.lib.utils as utils
import data.lib.communicate as com
import threading
from io import StringIO
from data.lib import env
from data.lib import printlib

print_adv = printlib.print_adv





def settings():
    """отображает окно настроек приложения.

        Позволяет изменять:
        - локализацию (язык интерфейса)
        - тему оформления
        - режим отладки
        для режима отладки добавляет дополнительные инструменты.
        """
    global locale, th, debug

    def lc_update(_name):
        global locale
        locale = utils.Locale(_name.replace('.json', ''))
        user_data['locale'] = _name.replace('.json', '')
        inter.build_ui()

    def th_update(_name):
        global th
        path = _name.replace('.json', '')
        print(f'th update into {path}')
        th = utils.Theme(path)
        inter.commit_theme(th)
        user_data['theme'] = path

    def change_val_widgets(val):
        global debug_widgets
        user_data['debug']['widgets'] = val
        debug_widgets = val

    def change_val(val):
        global debug
        user_data['debug']['enabled'] = val
        debug = val

    inter.settings(lc_update, th_update, change_val, change_val_widgets)


def create_chat():
    """окно создания нового чата.

        Позволяет:
        - выбирать контакты для добавления в чат
        - устанавливать тип чата (приватный/публичный)
        - создавать чат с выбранными параметрами
        """

    contacts = client.communicate({'type': 'get_contacts'})['c']

    def create(is_public, contacts_vars, link, _name):
        req = {'type': 'create_chat', 'users': [], 'is_public': is_public, 'name': _name}
        for _contact_name, _contact in contacts_vars.items():
            if _contact.get():
                req['users'].append(_contact_name)
        if is_public:
            req['public_id'] = link

        print_adv(req)

        print_adv(client.communicate(req))

    inter.create_chat(create, contacts)


def plugin_repo():
    _r = inter.showinfo('Info', 'Loading plugin list...')
    _plist = client.communicate({'type': 'get_plugin_list'})['l']



def search():
    def get_chats():
        global queue_updating
        queue_updating = False
        _a = client.recv_split_request({'type': 'get_public_chats_all', 'req_id': client.req_id})
        queue_updating = True
        return _a

    add_to_contacts = lambda user: client.send({'type': 'add_to_contacts', 'u': user})
    join = lambda link: client.send({'type': 'join', 'u': link})

    inter.search(get_chats(), join, add_to_contacts)


#class ChatManage(_ChatManage):
#    def __init__(self, chat_back):
#        s = client.communicate({'type': 'chat_manage_get_my_actions', 'chat': chats[self.chat_back]['link']}, waiting_action=inter.update)['a']
#        super().__init__()


def load_chat(_chat, menu=False):
    """загружает указанный чат в интерфейс.

        Args:
            _chat (str): название чата для загрузки
            menu (bool): load menu
        """
    global chat, chat_manage
    print_adv(f'[*] loading {_chat}')
    if not menu:
        chat = _chat
        chat_manage = False
    else:
        chat = ''
        chat_manage = True
    inter.build_ui()


def send_message():
    """отправляет сообщение в текущий активный чат.

       Returns:
           dict or none: данные отправленного сообщения или none при ошибке
       """
    msg = inter.get_msg() # gets message text

    print_adv(f'sending "{repr(msg)}" into "{chat}"', h=ui_log)
    if msg.strip() == "": # if msg is empty
        return None

    formated = format_message(msg, {'status': '...', 'status_full': 'Sending...'}, like_data=True)

    _message_bubble = inter.create_message(formated)
    try:
        _msg = client.communicate(format_message(msg), waiting_action=inter.update)

        if _msg is None:
            raise Exception('Failed to get server response')
        if len(_msg) > 800:
            raise Exception('Message is too long')
        adds = {'status': '.', 'status_full': 'Sent'}
    except Exception as _sending_exception:
        # formating unknown exception
        _sending_exception = str(_sending_exception.__class__)
        print_adv(traceback.format_exc())
        print_adv(_sending_exception)
        _ex_class = _sending_exception[_sending_exception.find("'") + 1:_sending_exception.rfind("'")]

        adds = {'status_full': f'(!) {locale.get("chat.error_send", "Error sending message")}: {_ex_class}', 'status': '(!)'}

    formated = format_message(msg, adds, True)
    try:
        inter.cfg_msg_bubble({'status': formated['status'], 'status_full': formated['status_full']}, _message_bubble)

        if formated['status'] == '(!)':
            inter.cfg_msg_bubble({'set_status_state_err': True}, _message_bubble)
    except Exception as _sm_wid_lost:
        inter.showinfo('Error', f'Failed to configure MessageBubble (YOUR MESSAGE IS SENT!) {_message_bubble}:\n{''.join(traceback.format_exception(_sm_wid_lost))}')
        print_adv(f'[SM] Send Error: message bubble widget lost ({_sm_wid_lost.__class__.__name__})')

    chats[chat]['msgs'].append(format_message(msg, adds, True))

    return formated


def format_message(msg, additional=None, like_data=False):
    _msg = {'type': 'msg', 'to_cl': f'{chats[chat]['link']}', 'from': client.username, 'text': msg, 'time': time.strftime("%H:%M:%S")}
    if additional is None:
        additional = {}
    for key, val in additional.items():
        _msg.update({key: val})
    if like_data:
        _msg.pop('type')
        _msg.pop('to_cl')
    return _msg


#def menu_state_loading():
#    global main_menu_state
#    while True:
#        curr_symb = '/'
#        mms_back = str(main_menu_state)
#        while main_menu_state_loading:
#            main_menu_state = f'{curr_symb} {mms_back}'
#            if curr_symb == '/':
#                curr_symb = '-'
#            elif curr_symb == '-':
#                curr_symb = '\\'
#            else:
#                curr_symb = '/'
#            time.sleep(0.05)
#        else:
#            main_menu_state = mms_back
#        time.sleep(0.5)

def backup_datas():
    """выполняет резервное копирование данных пользователя"""
    user_data.backup()


def get_chat_hist():
    global queue_updating, main_menu_state
    queue_updating = False
    main_menu_state = locale.get('m_lbl.cht_hist_update', 'Updating chat history...')
    _a = client.recv_split_request({'type': 'get_chat_hist', 'req_id': client.req_id})
    queue_updating = True
    return _a


def upload_chat_hist():
    global queue_updating
    client.send({'type': 'be_ready_for_chat_hist'})
    queue_updating = False
    time.sleep(0.5)
    hist_raw = json.dumps(chats)
    print_adv(hist_raw)
    ind = 0
    for i in range(0, math.ceil(len(hist_raw) / 1024)):
        print_adv(f'sending {hist_raw[ind: ind + 1024]}')
        try:
            client.send(hist_raw[ind: ind + 1024])
        except TypeError:
            return
        ind += 1024
        time.sleep(0.5)
    client.send('!!$%&END')
    queue_updating = True


def get_queue():
    global main_menu_state, chats
    if queue_updating:
        main_menu_state = locale.get('m_lbl.updating', 'Updating...')
        try:
            queue = client.communicate({'type': 'queue_get'}, waiting_action=inter.update)
        except OSError:
            print_adv('[QUEUE] Shutdown queue loop: OSError', h=sys.stderr)
            return -1
        print_adv(f'[QUEUE] {queue}', h=q_log)
        if queue is not None and isinstance(queue, dict):
            for i in queue['q']:
                if i['type'] == 'new_chat':
                    chats[i['name']] = {'msgs': [], 'link': i['link'], 'users': i['users']}
                    inter.build_ui()
                if i['type'] == 'msg':
                    print_adv(i)
                    _copy = i.copy()
                    for _chat_name, _data in chats.items():
                        if _data['link'] == i['to_cl']:
                            i.pop('type')
                            chats[_chat_name]['msgs'].append(i)
                if i['type'] == 'force_chat_hist_update':
                    chats = get_chat_hist()

        main_menu_state = locale.get('m_lbl.program_title', 'MSGR QWS')
    else:
        print_adv('[QUEUE] skipping by queue_updating = False', h=q_log)
    return 0


def gvar(__name):
    return globals().get(__name, None)


def svar(__name, __value):
    globals()[__name] = __value


def load_plugs():
    _print = lambda *e: print_adv(*e, h=plugin_api_log)
    _print('Loading plugins')
    _plugins_l_dir = os.listdir('./data/plugins')
    _print(f'Detected plugins: {len(_plugins_l_dir)}')
    for i in _plugins_l_dir:
        _meta = json.load(open(f'./data/plugins/{i}/meta.json'))
        _print(f'package name: {_meta['pack_name']}, name: "{_meta['name']}"')
        if 'work_dir' in _meta:
            sys.path.append(_meta['work_dir'])
        code_plg = open(f'data/plugins/{i}/{_meta['pack_name']}.py').read()
        _print('checking plugin suspicious actions')
        sus_actions_detected = []

        #if 'exec' in code_plg:
        #    sus_actions_detected.append('Any code executing')
        if 'os.remove' in code_plg:
            sus_actions_detected.append('Removing files')
        if 'subprocess.run' in code_plg:
            sus_actions_detected.append('Running commands in cmd')


        _fl = importlib.import_module(f'data.plugins.{i}.{_meta['pack_name']}')
        if sus_actions_detected:
            _fl.update_var = lambda s, g: None
            def lock_exec():
                raise Exception(f'Suspicious activity in plugin {_meta['pack_name']}: {', '.join(sus_actions_detected)}')
            _fl.execute_code = lock_exec
        _fl.update_var(svar, gvar)
        try:
            _fl.execute_code()
        except Exception as _plugin_exec_err:
            print_adv(f'[sERR-Wrp-{plugin_api_log.name}] Exception detected at loading plugin: {_plugin_exec_err}, full traceback shown in ui', h=sys.stderr)
            inter.showinfo('Error', ''.join(traceback.format_exception(_plugin_exec_err)))

if __name__ == '__main__':
    """основной блок запуска приложения.

        инициализирует:
        - систему логирования
        - пользовательские данные
        - графический интерфейс
        - сетевое подключение
        - фоновые процессы
        """
    class Log:
        """класс для перехвата и буферизации вывода в консоль."""
        def __init__(self, original, _name='log', use_file=True):
            self.original = original
            self.buffer = StringIO()
            self._print_lib_compatible = True
            self.name = _name
            if use_file:
                with open(f'./data/logs/{_name}.log', 'w'):
                    pass
                self._fl = open(f'./data/logs/{_name}.log', 'a', errors='replace')
            else:
                self._fl = None
            env.env[f'LogPrintLib{_name}'] = self

        def write(self, dt):
            if dt not in ['', ' ', '\n', 'None']:
                try:
                    if self.read()[-1] != '\n':
                        self.original.write(f'\n')
                        self.buffer.write(f'\n')
                except IndexError:
                    pass
                self.original.write(f'{dt}')
                self.buffer.write(f'{dt}\n')
                if self._fl is not None:
                    self._fl.write(f'{dt}')
                    self._fl.flush()

        def read(self):
            self.buffer.seek(0)
            return self.buffer.read()

        def flush(self):
            pass


    sys.stdout = Log(sys.__stdout__, _name='STDOUT')
    sys.stderr = Log(sys.__stderr__, _name='STDERR')
    # раздельное логирование
    main_log = Log(sys.stdout, _name='Main')
    printlib.print_lib_root = main_log
    q_log = Log(sys.stdout, _name='Queue')
    ui_log = Log(sys.stdout, _name='Interface')
    sock = Log(sys.stdout, _name='Socket')
    plugin_api_log = Log(sys.stdout, _name='PluginAPI')

    com.refresh_log()

    queue_updating = True

    def excepthook(x, y=None, z=None):
        printlib.printin(f'==== TRACEBACK {x} ====\n{''.join(traceback.format_exception(x, y, z))}==== END ====', sys.stderr)

    def threading_excepthook(args, /):
        printlib.printin(f'==== TRACEBACK {args.exc_type} ====\n{''.join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))}==== END ====', sys.stderr)

    sys.excepthook = excepthook
    threading.excepthook = threading_excepthook

    print_adv('[*] MSGR-QWS Kernel, 2025')
    print_adv('! ! ! TYPE "exit" to kill kernel ! ! !')
    def exit_wrp():
        while True:
            try:
                if 'exit' in input():
                    print('CRASHING APPLICATION')
                    os.kill(os.getpid(), signal.SIGTERM)
                time.sleep(1)
            except UnicodeError:
                print_adv('Failed - unicode error (stop)')
    threading.Thread(target=exit_wrp, daemon=True).start()


    if platform.system() == 'Windows':
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception as _ctypes_error:
            print_adv(f'[*] Failed to SetProcessDpiAwareness: {_ctypes_error}')

    chat = ''
    chat_manage = True

    print_adv('[*] loading user data')
    name = 'user_data'
    if '--change-userdata' in sys.argv:
        name = sys.argv[sys.argv.index('--change-userdata') + 1]
    user_data = utils.UserData(open(f'./data/{name}.json', 'r'))

    print_adv('[*] checking keys')
    need_keys = {'theme': '', 'locale': '', 'username': '', 'password': '', 'addr': [], 'debug': {'enabled': False, 'widgets': False}, 'curr_interface': 'TkInterface'}
    for _key in need_keys:
        if _key not in user_data.keys():
            print_adv(f'[*] setting default value for {_key}')
            user_data[_key] = need_keys[_key]
    print_adv('[*] keys checked!')

    debug = user_data['debug']['enabled']
    debug_widgets = user_data['debug']['widgets']
    if debug == '':
        user_data['debug'] = {}
        debug = False

    chats = {}
    _interface = importlib.import_module(f'data.lib.interface.{user_data['curr_interface']}.main')
    _interface.update_var(svar, gvar)

    inter = _interface.Interface(lambda: chats.copy(), {'functions': [lambda d, c: client.communicate({'type': 'delete_user', 'delete_user': d, 'chat': c}),
                                                                                lambda d, c: client.communicate({'type': 'add_admin', 'add_admin': d, 'chat': c}),
                                                                                lambda d, c: client.communicate({'type': 'remove_admin', 'remove_admin': d, 'chat': c}),
                                                                                lambda c, *u: client.communicate({'c': u, 'type': 'add_users', 'chat': c}),
                                                                                lambda: client.communicate({'type': 'get_contacts'})['c']], 'actions': lambda c: client.communicate({'type': 'chat_manage_get_my_actions', 'chat': c})['a']})
    inter.loading_lbl_interface()

    print_adv('[*] loading theme')
    th = utils.Theme(user_data['theme'])
    globals()['th'] = th
    inter.commit_theme(th)

    print_adv('[*] loading locale')
    locale = utils.Locale(user_data['locale'])
    globals()['locale'] = locale

    # global widgets
    #message_entry = Text()
    #root_frame_for_chats = Frame()
    #main_container = MessageBubble()
    #send_part = Frame()
    #top_menu = Frame()
    #top_menu.init_completed = False
    #main_menu_state_lbl = Label()

    #main_menu_state_var = StringVar(root)
    main_menu_state = 'MSGR QWS'
    session_key = ''

    print_adv('[*] connecting to server')
    print_adv('[*] getting addr from git')
    try:
        tmp = requests.get().text.split('\n')[0].split(':')
        user_data['addr'] = [tmp[0], int(tmp[1])]
    except Exception as _git_get_ex:
        print_adv(f'[!!] failed to get addr from git: {_git_get_ex.__class__}', h=sys.stderr)

    client = com.Server(user_data['addr'][0], user_data['addr'][1], user_data['username'], user_data['password'], inter.update, lambda e: showerror('Server Side Error', e), False)

    inter.update()

    if user_data['username'] == '' or user_data['password'] == '':
        def confirm(u, p):
            user_data['username'] = u
            user_data['password'] = p

        inter.serv_select(confirm)


    def start_server_th():
        global main_menu_state, chats, session_key
        timeout = 1
        connected = False
        while timeout < 60 or not connected:
            if timeout > 1:
                client.recreate_sock()
            time.sleep(timeout)
            main_menu_state = locale.get('m_lbl.connecting_state', 'Connecting')
            try:
                session_key = utils.randgen()
                client.connect()
                main_menu_state = locale.get('m_lbl.auth_state', 'Authenticating')
                client.auth()
                break
            except Exception as _ex_srv:
                print_adv(_ex_srv)
                timeout *= 2
                if debug:
                    printlib.printin(f'[debug] Error connecting to server:\n{traceback.format_exc()}', sys.stderr)
                else:
                    print_adv('[ce] failed to connect to the server', h=sys.stderr)
                main_menu_state = locale.get('m_lbl.failed_to_connect_state', 'Failed to connect') + f' {locale.get('m_lbl.reconnect_in_p1', 'Re-connect in')} {timeout} {locale.get('seconds', 'seconds')}'
        print_adv('connected')
        main_menu_state = locale.get('m_lbl.updating', 'Updating...')
        if debug:
            main_menu_state += ' downloading chat history...'
        chats = get_chat_hist()
        inter.build_ui()
        main_menu_state = locale.get('m_lbl.program_title', 'MSGR QWS')
        time.sleep(5)
        inter.create_loop(get_queue, 5000)
        inter.create_loop(get_chat_hist, 60000)


    threading.Thread(target=start_server_th, daemon=True).start()


    #threading.Thread(target=menu_state_loading, daemon=True).start()
    utils.create_loop(backup_datas, 5)
    #root.create_loop(get_chat_hist, 30000)

    load_plugs()


    inter.start()

    print_adv('[*] exiting')
    user_data.backup()
    print_adv('[*] destroying window')
    inter.destroy()
    print_adv('[*] bye')
else:
    print_adv(__name__)
    print_adv('not main, skip')