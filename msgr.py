import ctypes
import json
import math
import os
import platform
import signal
import sys
import time
import traceback
from io import StringIO
from tkinter import *
import requests
import data.lib.utils as utils
import data.lib.communcate as com
import threading
from data.lib import ui
from data.lib.ui import Win, CustomWindow
from data.lib.printlib import print_adv, printin, main_log as print_lib_main_log

def settings():
    """отображает окно настроек приложения.

        Позволяет изменять:
        - локализацию (язык интерфейса)
        - тему оформления
        - режим отладки
        для режима отладки добавляет дополнительные инструменты.
        """
    global locale, th, debug
    settings_data_frame = show(locale.get('base.settings', 'Settings'))
    settings_data_frame.root_frame.place_forget()
    settings_data_frame.root_frame.place(x=0, y=0, anchor='nw', relheight=1.0)


    def lc_update(event):
        global locale
        locale = utils.Locale(event.widget.get().replace('.json', ''))
        user_data['locale'] = event.widget.get().replace('.json', '')
        root.destroy_children()
        build_ui()

    def th_update(event):
        global th
        path = event.widget.get().replace('.json', '')
        print(f'th update into {path}')
        th = utils.Theme(path)
        root.option_add('*highlightColor', th.fg, 'widgetDefault')
        root.option_add('*highlightBackground', th.fg)
        root.option_add('*Frame.highlightColor', th.fg, 'widgetDefault')
        root.option_add('*Background', th.bg, 'widgetDefault')
        root.option_add('*Foreground', th.fg, 'widgetDefault')
        root.option_add('*Font', th.font, 'widgetDefault')
        root.configure(bg=th.bg)
        user_data['theme'] = path
        root.configure_children(bg=th.bg, fg=th.fg, font=th.font, highlightcolor=th.fg, highlightbackground=th.fg)

    lc = ui.Combobox(settings_data_frame, values=os.listdir('./data/locale'), bg=th.bg, fg=th.fg)
    lc.entry.insert("end", locale.get('settings.locale_txt', 'Localization'))
    lc.bind('<<ComboboxSelected>>', lc_update)
    lc.entry.configure(state='readonly')
    lc.pack()

    th_box = ui.Combobox(settings_data_frame, values=os.listdir('./data/theme'), bg=th.bg, fg=th.fg)
    th_box.entry.insert("end", locale.get('settings.theme_txt', 'Theme'))
    th_box.bind('<<ComboboxSelected>>', th_update)
    th_box.entry.configure(state='readonly')
    th_box.pack()
    def change_val():
        global debug
        if var.get():
            user_data['debug']['enabled'] = True
            debug = True
        else:
            user_data['debug']['enabled'] = False
            debug = False

    var = BooleanVar(root, value=user_data['debug']['enabled'])
    dbg_check = Checkbutton(settings_data_frame, text='debug', command=change_val, variable=var)
    dbg_check.pack()

    if debug:
        def show_errors():
            w = show('errors')
            errs = Listbox(w)
            errs.pack(fill='both', expand=True)
            traces = []
            trace_buffer = ''
            for i in sys.stdout.read().split('\n'):
                if '[!!]' in i:
                    errs.insert('end', f'ERROR: {i}')
                elif '[!]' in i:
                    errs.insert('end', f'WARN: {i}')
            for i in sys.stderr.read().split('\n'):
                if trace_buffer != '':
                    trace_buffer += i
                if i == '==== END ====':
                    traces.append(trace_buffer)
                    trace_buffer = ''
                if '==== TRACEBACK' in i:
                    trace_buffer += i + '\n'
            showinfo('traces', '\n'.join(traces))


        Button(settings_data_frame, text='[debug] restart terminal', command=lambda: threading.Thread(target=terminal_thread, daemon=True).start()).pack()
        Button(settings_data_frame, text='errors', command=show_errors).pack()


def show(title='pop'):
    """создает и отображает модальное окно.

        args:
            title (str): заголовок окна. по умолчанию 'pop'.

        returns:
            frame: контейнер для содержимого окна.
        """

    _root = ui.Popup(title=title)
    return _root


def showinfo(title, text):
    Label(show(title), text=text).pack(anchor='nw')


def create_chat():
    """окно создания нового чата.

        Позволяет:
        - выбирать контакты для добавления в чат
        - устанавливать тип чата (приватный/публичный)
        - создавать чат с выбранными параметрами
        """
    def create():
        req = {'type': 'create_chat', 'users': [], 'is_public': is_public, 'name': name_entry.get()}
        for _contact_name, _contact in contacts_vars.items():
            if _contact.get():
                req['users'].append(_contact_name)
        if is_public:
            req['public_id'] = link_entry.get()

        print_adv(req)

        print_adv(client.communicate(req))

    win = show('chat adding')
    win.pack_propagate(True)
    Label(win, text='Add Users').pack()
    contacts_select = ui.ListFrames(master=win)
    contacts_vars = {}


    for contact in client.communicate({'type': 'get_contacts'})['c']:
        contacts_vars[contact] = BooleanVar(master=win, value=False)
        w = Checkbutton(contacts_select.for_w, text=contact, variable=contacts_vars[contact])
        w.pack(anchor='nw')

    contacts_select.pack()
    Label(win, text='Tag type').pack()
    def private_set():
        nonlocal is_public
        is_public = False
        public_var.set(False)
        private_var.set(True)
        for_link_fr.pack_forget()

    def public_set():
        nonlocal is_public
        is_public = True
        public_var.set(True)
        private_var.set(False)
        for_link_fr.pack(fill='x', expand=True)

    for_checks_fr = Frame(win)
    for_link_fr = Frame(win)
    for_name_fr = Frame(win)

    name_entry = Entry(for_name_fr)
    name_lbl = Label(for_name_fr, text='Name: ')
    name_lbl.pack(anchor='nw', side='left')
    name_entry.pack(anchor='nw', side='right')

    link_entry = Entry(for_link_fr)
    link_lbl = Label(for_link_fr, text='Public link for you chat: ')
    link_lbl.pack(anchor='nw', side='left')
    link_entry.pack(anchor='nw', side='right')

    is_public = False
    private_var = BooleanVar(value=not is_public)
    public_var = BooleanVar(value=is_public)
    private_check = Checkbutton(for_checks_fr, text='Private', variable=private_var, command=private_set)
    private_check.pack(anchor='nw', side='left')
    public_check = Checkbutton(for_checks_fr, text='Public', variable=public_var, command=public_set)
    public_check.pack(anchor='nw', side='right')
    for_checks_fr.pack()
    for_name_fr.pack(fill='x', expand=True)



    Button(win, text='Create', command=create).pack(fill='x', expand=True, side='bottom')


class MessageBubble(Frame):
    for_w: Frame
    err_status: Label

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            highlightcolor=th.fg,
            highlightbackground=th.fg
        )



def create_message(_msg, main_cont):
    print_adv(f'[CM] creating {_msg} at {main_cont}', h=ui_log)
    _w = MessageBubble(main_cont.for_w, highlightthickness=2)
    Label(_w, text=_msg['from'], font=(th.font[0], int(th.font[1] - 1))).pack(anchor='nw')
    Label(_w, text=_msg['text'], justify='left').pack(side='left')
    Label(_w, text=_msg['time'], font=(th.font[0], int(th.font[1] - 1))).pack(anchor='se', side='left')
    if 'status' in _msg:
        err = Label(_w, text=_msg['status'])
        if _msg['status'] == '(!)':
            err.config(fg='red')
        if 'status_full' not in _msg:
            _msg['status_full'] = '(!) Unknown'
        err.status_full = _msg['status_full']
        err.pack(anchor='se', side='left')

        def show_err(event):
            if not hasattr(err, 'popup'):
                event.widget.popup = None
            if err.popup is None:
                err.popup = Label(root, text=err.status_full, highlightthickness=2, justify='left')
                err.popup.place(x=err.winfo_rootx() - err.winfo_toplevel().winfo_rootx(),
                                y=err.winfo_rooty() - err.winfo_toplevel().winfo_rooty(), anchor='ne')
            else:
                err.popup.destroy()
                err.popup = None

        err.bind('<Enter>', show_err)
        err.bind('<Leave>', show_err)
        _w.err_status = err
    if _msg['from'] not in [user_data['username'], 'You']:
        _w.pack(pady=5, padx=5, anchor='w')
    else:
        _w.pack(pady=5, padx=5, anchor='e')
    return _w


def search():
    def get_chats():
        global queue_updating
        queue_updating = False
        _a = client.recv_split_request({'type': 'get_public_chats_all', 'req_id': client.req_id})
        queue_updating = True
        return _a

    _search_pop = ui.Popup(title=locale.get('base.search', 'Search'))
    chats_list = ui.ListFrames(master=_search_pop)
    chats_list.pack(fill='both', expand=True)
    s = get_chats()
    print(f'all public chats {s}')
    def show_user_profile(e):
        prof = ui.Popup(title=f'User: {e.widget["text"]}')
        prof.pack_propagate(False)
        Label(prof, text=e.widget['text']).pack(anchor='nw')
        Button(prof, text='add to contacts', command=lambda: client.send({'type': 'add_to_contacts', 'u': e.widget['text']})).pack(side='bottom')
    def show_chat_profile(e):
        prof = ui.Popup(title=f'Chat: {e.widget["text"]}')
        prof.pack_propagate(False)
        Label(prof, text=e.widget['text']).pack(anchor='nw')
        if debug:
            chat_inf = ''
            for _i in e.widget.chat_data:
                chat_inf += f'{_i}: {e.widget.chat_data[_i]}\n'
            Label(prof, text=f'chat info: {chat_inf}').pack(anchor='nw')
        Button(prof, text='join',
               command=lambda: client.send({'type': 'join', 'u': e.widget.chat_data['link']})).pack(side='bottom')
    for i in s['h']:
        if isinstance(i, str):
            _w = Label(_search_pop, text=str(i))
            _w.bind('<Button-1>', show_user_profile)
            _w.pack(fill='x', expand=True, padx=5, pady=3)
        elif isinstance(i, dict):
            _w = Label(_search_pop, text=str(i['name']))
            _w.chat_data = i.copy()
            _w.bind('<Button-1>', show_chat_profile)
            _w.pack(fill='x', expand=True, padx=5, pady=3)




def build_ui():
    """собирает и обновляет основной пользовательский интерфейс.

        В зависимости от текущего состояния (выбран чат или нет) отображает:
        - список чатов
        - окно сообщений выбранного чата
        - панель ввода сообщений
        """
    global message_entry, root_frame_for_chats, main_container, send_part, top_menu, main_menu_state_lbl
    if debug:
        root.config(bg='blue')
    _recreate_top_menu = False
    if hasattr(top_menu, 'init_completed'):
        _recreate_top_menu = True

    try:
        top_menu.pack(fill='x')
        top_menu.pack_forget()
    except TclError:
        _recreate_top_menu = True

    if _recreate_top_menu:
        top_menu.destroy()

        top_menu = Frame(highlightthickness=2)
        main_menu_state_lbl = Label(top_menu, textvariable=main_menu_state_var)
        settings_butt = Button(top_menu, text=locale.get('base.settings', 'Settings'), command=settings)

        search_button = Button(top_menu, text=locale.get('base.search', 'Search'), command=search)
        search_button.place(rely=0, relx=0, anchor='nw', relheight=1.0)

        settings_butt.place(rely=1.0, relx=1.0, anchor='se', relheight=1.0)
        main_menu_state_lbl.pack(fill='y', expand=True)
    else:
        _th = Label()
        ui.configure_children_static(top_menu, bg=_th['bg'], fg=_th['fg'], font=_th['font'], highlightcolor=_th['highlightcolor'])


    find_chats_button = Button(root, text='//', command=create_chat)

    send_part.destroy()
    main_container.destroy()

    if chat == '':
        top_menu.pack(fill='x')
        main_container = ui.ListFrames()
        main_container.pack(fill='both', expand=True)
        #main_container.for_w.pack_propagate(False)
        if debug:
            main_container.configure(bg='red')
            main_container.for_w.configure(bg='green')

        #chat_selects = {}

        if chats != {}:
            for chat_name in chats.keys():
                w = Label(main_container.for_w, text=chat_name, highlightthickness=2)
                w.pack(pady=5, padx=5, fill='x', ipady=10)
                w.bind('<Button-1>', lambda e: load_chat(e.widget['text']))
            print_adv(main_container.winfo_width(), main_container.canvas.winfo_width(), main_container.for_w.winfo_width())
        else:
            Label(main_container.for_w, text=locale.get('chat_menu.start_lbl', 'Create or find chats with "//" button')).pack(fill='both', expand=True)

        find_chats_button.place(relx=1.0, rely=1.0, anchor='se')
        find_chats_button.lift()
    else:
        top_menu.pack_forget()
        send_part.destroy()
        main_container.destroy()
        top_menu_chat = Frame(highlightthickness=2)
        Label(top_menu_chat, text=chat).pack(fill='y', expand=True)
        def back():
            top_menu_chat.pack_forget()
            load_chat('')
        def chat_menu():
            chat_back = chat
            _w = show(f'Chat manage: {chat_back}')
            available_actions = client.communicate({'type': 'chat_manage_get_my_actions', 'chat': chats[chat_back]['link']})['a']
            if debug:
                Label(_w, text='\n'.join(available_actions), justify='left').pack(anchor='nw')
            _actions = ui.ListFrames(master=_w)

            def exec_action(event):
                def add():
                    _invite_w.destroy()
                    req = {'c': [], 'type': 'add_users', 'chat': chats[chat_back]['link']}
                    for _name, _value in contacts_vars.items():
                        if _value.get():
                            req['c'].append(_name)
                    if debug:
                        showinfo('13', f'sent {req}')
                    client.send(req)
                print_adv(f'chat menu action: {event.widget.action_name}')
                if event.widget.action_name == 'invite_users':
                    _invite_w = show(f'Invite into {chat_back}')
                    Label(_invite_w, text='Add Users').pack()
                    contacts_select = ui.ListFrames(master=_invite_w)
                    contacts_vars = {}

                    for contact in client.communicate({'type': 'get_contacts'})['c']:
                        contacts_vars[contact] = BooleanVar(master=_invite_w, value=False)
                        _chb = Checkbutton(contacts_select.for_w, text=contact, variable=contacts_vars[contact])
                        _chb.pack(anchor='nw')

                    contacts_select.pack()
                    Button(_invite_w, text='add', command=add).pack()


            for i in available_actions:
                _a = Button(_actions.for_w, text=i)
                _a.action_name = i
                _a.bind('<Button-1>', exec_action)
                _a.pack(anchor='nw')
            _actions.pack()


        Button(top_menu_chat, text='<--', command=back).place(x=0, y=0, relheight=1.0)
        Button(top_menu_chat, text='Menu', command=chat_menu).place(relx=1.0, y=0, relheight=1.0, anchor='ne')
        top_menu_chat.pack(fill='x')

        send_part = Frame(highlightthickness=2)
        message_entry = Text(send_part, autoseparators=True, height=1)
        message_entry.pack(fill='both', expand=True, side='left')
        def wrp():
            _msg = send_message()
            main_container.scroll_to_bottom()
        Button(send_part, text='^\n|', command=wrp).pack(fill='y', expand=True, side='right')

        main_container = ui.ListFrames()
        main_container.pack(fill='both', expand=True, anchor='nw')
        send_part.pack(side='bottom', fill='x')
        if debug:
            main_container.configure(bg='red', highlightthickness=5)
            main_container.canvas.configure(bg='yellow')
            main_container.for_w.configure(bg='green')

       # chat_selects = {}

        if chats[chat]:
            for msg in chats[chat]['msgs']:
                create_message(msg, main_container)
            print_adv(main_container.winfo_width(), main_container.canvas.winfo_width(), main_container.for_w.winfo_width())
        else:
            Label(main_container.for_w,
                  text=locale.get('chat.empty', 'No messages in this chat...')).pack(fill='both',expand=True)

        main_container.scroll_to_bottom()

    ui.lift_popups()

def load_chat(_chat):
    """загружает указанный чат в интерфейс.

        Args:
            _chat (str): название чата для загрузки
        """
    global chat
    print_adv(f'[*] loading {_chat}')
    chat = _chat
    build_ui()


def send_message():
    """отправляет сообщение в текущий активный чат.

       Returns:
           dict or none: данные отправленного сообщения или none при ошибке
       """
    msg = message_entry.get("0.0", 'end') # gets message text

    print_adv(f'sending "{msg}" into "{chat}"', h=ui_log)
    if msg.strip() == "": # if msg is empty
        return None

    formated = format_message(msg, {'status': '...', 'status_full': 'Sending...'}, like_data=True)

    _message_bubble = create_message(formated, main_container)
    try:
        _msg = client.communicate(format_message(msg), waiting_actions=root.update)

        if _msg is None:
            raise Exception('Failed to get server response')
        if len(_msg) > 800:
            raise Exception('Message is too long')
        adds = {'status': '.', 'status_full': 'Sent'}
    except Exception as _ex:
        # formating unknown exception
        _ex = str(_ex.__class__)
        print_adv(traceback.format_exc())
        print_adv(_ex)
        _ex_class = _ex[_ex.find("'") + 1:_ex.rfind("'")]

        adds = {'status_full': f'(!) {locale.get("chat.error_send", "Error sending message")}: {_ex_class}', 'status': '(!)'}

    message_entry.delete('0.0', END)

    formated = format_message(msg, adds, True)

    _message_bubble.err_status['text'] = formated['status']
    _message_bubble.err_status.status_full = formated['status_full']

    if formated['status'] == '(!)':
        _message_bubble.err_status.config(fg='red')

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


def update_menu_state():
    """обновляет состояние главного меню."""
    if main_menu_state_var.get() != main_menu_state:
        print_adv(f'[*] updating main menu state to {main_menu_state}', h=ui_log)
        main_menu_state_var.set(main_menu_state)


def backup_datas():
    """выполняет резервное копирование данных пользователя"""
    user_data.backup()





def get_chat_hist():
    global queue_updating
    queue_updating = False
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
    global main_menu_state
    if queue_updating:
        main_menu_state = locale.get('m_lbl.updating', 'Updating...')
        try:
            queue = client.communicate({'type': 'queue_get'}, waiting_actions=root.update)
        except OSError:
            print_adv('[QUEUE] Shutdown queue loop: OSError', h=sys.stderr)
            return -1
        print_adv(f'[QUEUE] {queue}')
        if queue is not None and isinstance(queue, dict):
            for i in queue['q']:
                if i['type'] == 'new_chat':
                    chats[i['name']] = {'msgs': [], 'link': i['link'], 'users': i['users']}
                    build_ui()
                if i['type'] == 'msg':
                    print_adv(i)
                    _copy = i.copy()
                    for _chat_name, _data in chats.items():
                        if _data['link'] == i['to_cl']:
                            i.pop('type')
                            create_message(i, main_container)
                            chats[_chat_name]['msgs'].append(i)

        def wrp(non):
            print(non)
            global main_menu_state
            main_menu_state = locale.get('m_lbl.program_title', 'MSGR QWS')
        root.after(500, wrp, None)
    else:
        print_adv('[QUEUE] skipping by queue_updating = False', h=q_log)
    return 0


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
            self.name = _name
            if use_file:
                with open(f'./data/logs/{_name}.log', 'w'):
                    pass
                self._fl = open(f'./data/logs/{_name}.log', 'a', errors='replace')
            else:
                self._fl = None
            print_adv(f'Init {_name} Log', h=self)

        def write(self, dt):
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


    sys.stdout = Log(sys.__stdout__, _name='stdout')
    sys.stderr = Log(sys.__stderr__, _name='stderr')
    # раздельное логирование
    main_log = Log(sys.stdout, _name='MAIN')
    print_lib_main_log = main_log
    q_log = Log(sys.stdout, _name='QUEUE')
    ui_log = Log(sys.stdout, _name='Interface')
    unknown = Log(sys.stdout, _name='UNK')

    queue_updating = True

    def excepthook(x, y=None, z=None):
        printin(f'==== TRACEBACK {x} ====\n{''.join(traceback.format_exception(x, y, z))}==== END ====', sys.stderr)

    def threading_excepthook(args, /):
        printin(f'==== TRACEBACK {args.exc_type} ====\n{''.join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))}==== END ====', sys.stderr)

    sys.excepthook = excepthook
    threading.excepthook = threading_excepthook

    print_adv('[*] MSGR-QWS, 2025')
    print_adv('! ! ! TYPE "exit" to close application ! ! !')
    def exit_wrp():
        while True:
            if 'exit' in input():
                print('CRASHING APPLICATION')
                os.kill(os.getpid(), signal.SIGTERM)
            time.sleep(1)
    threading.Thread(target=exit_wrp, daemon=True).start()


    if platform.system() == 'Windows':
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception as _ctypes_error:
            print_adv(f'[*] Failed to SetProcessDpiAwareness: {_ctypes_error}')

    chat = ''

    print_adv('[*] * - info, ! - warning, !! - error')
    print_adv('')

    print_adv('[*] loading user data')
    name = 'user_data'
    if '--change-userdata' in sys.argv:
        name = sys.argv[sys.argv.index('--change-userdata') + 1]
    user_data = utils.UserData(open(f'./data/{name}.json', 'r'))

    print_adv('[*] checking keys')
    need_keys = {'theme': '', 'locale': '', 'username': '', 'password': '', 'addr': [], 'debug': {'enabled': False, 'widgets': False}}
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

    root = Win()
    root.geometry('900x500')
    root.title('MSGR QWS')
    root.curr_container = None

    print_adv('[*] loading theme')
    th = utils.Theme(user_data['theme'])
    root.option_add('*highlightColor', th.fg, 'widgetDefault')
    root.option_add('*highlightBackground', th.fg)
    root.option_add('*Background', th.bg, 'widgetDefault')
    root.option_add('*Foreground', th.fg, 'widgetDefault')
    root.option_add('*Font', th.font, 'widgetDefault')
    root.configure(bg=th.bg)

    print_adv('[*] loading locale')
    locale = utils.Locale(user_data['locale'])

    Label(text='Loading...').place(x=0, y=0)

    # global widgets
    message_entry = Text()
    root_frame_for_chats = Frame()
    main_container = MessageBubble()
    send_part = Frame()
    top_menu = Frame()
    top_menu.init_completed = False
    main_menu_state_lbl = Label()

    main_menu_state_var = StringVar(root)
    main_menu_state = 'MSGR QWS'
    chats = {}
    session_key = ''

    print_adv('[*] connecting to server')
    print_adv('[*] getting addr from git')
    tmp = requests.get("https://raw.githubusercontent.com/zcveo5/sturdy-octo-rotary-phone/main/addr.txt").text.split('\n')[0].split(':')
    user_data['addr'] = [tmp[0], int(tmp[1])]

    client = com.Server(user_data['addr'][0], user_data['addr'][1], user_data['username'], user_data['password'])

    root.update()

    if user_data['username'] == '' or user_data['password'] == '':
        def confirm():
            user_data['username'] = user_entry.get()
            user_data['password'] = pass_entry.get()
            server_popup.destroy()
            root.quit()

        server_popup = show()
        user_entry = Entry(server_popup)
        user_entry.pack()
        pass_entry = Entry(server_popup)
        pass_entry.pack()
        Button(server_popup, text=locale.get('base.confirm', 'Confirm'), command=confirm).pack()
        root.mainloop()

    def start_server_th():
        global main_menu_state, chats, session_key
        main_menu_state = locale.get('m_lbl.connecting_state', 'Connecting')
        try:
            session_key = utils.randgen()
            client.connect()
        except Exception as _ex:
            print_adv(_ex)
            if debug:
                printin(f'[debug] Error connecting to server:\n{traceback.format_exc()}', sys.__stderr__)
            else:
                print_adv('[connectError] failed to connect to the server', h=sys.stderr)
            main_menu_state = locale.get('m_lbl.failed_to_connect_state', 'Failed to connect')
            time.sleep(2)
        print_adv('connected')
        main_menu_state = locale.get('m_lbl.updating', 'Updating...')
        if debug:
            main_menu_state += ' downloading chat history...'
        chats = get_chat_hist()
        main_menu_state = locale.get('m_lbl.program_title', 'MSGR QWS')
        root.create_loop(get_queue, 5000)
        build_ui()

    if debug:
        def terminal_thread():
            try:
                def execute():
                    namespace_plus = globals()
                    def set_var(_name, value):
                        globals()[_name] = value
                    namespace_plus.update({'svar': set_var})
                    exec(command.get("0.0", "end"), globals(), locals())
                ter = Win()
                ter.title('terminal')
                command = Text(ter)
                Button(ter, text='exec', command=execute).pack()
                is_recv_locked = Label(ter)
                is_recv_locked.place(x=0, y=0)
                command.pack()
                def wrp():
                    is_recv_locked['text'] = str(True)
                ter.create_loop(wrp, 500)
                ter.mainloop()
            except Exception as _ter_ex:
                print_adv(f'[terminal error] {_ter_ex}', h=sys.stderr)


        threading.Thread(target=terminal_thread, daemon=True).start()

    threading.Thread(target=start_server_th, daemon=True).start()

    root.after(250, print_adv, "[*] starting loops")

    root.create_loop(update_menu_state, 500)
    root.create_loop(backup_datas, 5000)
    #root.create_loop(get_chat_hist, 30000)

    build_ui()
    def _exit_wrapper():
        global main_menu_state
        uploading_popup = Frame(root, highlightthickness=4)
        uploading_popup.pack_propagate(True)
        Label(uploading_popup, text=locale.get('m_lbl.uploading', 'Uploading...')).pack()
        uploading_popup.place(relx=0.5, rely=0.5, anchor='center')
        root.update()
        root.quit()
    root.protocol('WM_DELETE_WINDOW', _exit_wrapper)
    root.mainloop()

    print_adv('[*] exiting')
    user_data.backup()
    print_adv('[*] uploading chat history')
    upload_chat_hist()
    print_adv('[*] destroying window')
    root.destroy()
    print_adv('[*] bye')
else:
    print_adv(__name__)
    print_adv('not main, skip')