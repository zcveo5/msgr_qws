import ctypes
import json
import os
import platform
import random
import sys
import traceback
from io import StringIO
from tkinter import *
from tkinter.ttk import Combobox
import requests
import data.lib.utils as utils
import data.lib.communcate as com
import threading
import time

from data.lib import jsoncrypt, ui
from data.lib.ui import Win


def settings():
    global locale, th
    settings_data_frame = show(locale.get('base.settings', 'Settings'))
    settings_data_frame.master.place_forget()
    settings_data_frame.master.place(x=0, y=0, anchor='nw', relheight=1.0)


    def lc_update(event):
        global locale
        locale = utils.Locale(event.widget.get().replace('.json', ''))
        user_data['locale'] = event.widget.get().replace('.json', '')
        root.destroy_children()
        build_ui()

    def th_update(event):
        global th
        path = event.widget.get().replace('.json', '')
        th = utils.Theme(path)
        root.option_add('*Background', th.bg)
        root.option_add('*Foreground', th.fg)
        root.option_add('*Font', th.font)
        root.configure(bg=th.bg)
        user_data['theme'] = path
        root.configure_children(bg=th.bg, fg=th.fg, font=th.font)

    lc = Combobox(settings_data_frame, values=os.listdir('./data/locale'))
    lc.insert("end", locale.get('settings.locale_txt', 'Localization'))
    lc.bind('<<ComboboxSelected>>', lc_update)
    lc.configure(state='readonly')
    lc.pack()

    th_box = Combobox(settings_data_frame, values=os.listdir('./data/theme'))
    th_box.insert("end", locale.get('settings.theme_txt', 'Theme'))
    th_box.bind('<<ComboboxSelected>>', th_update)
    th_box.configure(state='readonly')
    th_box.pack()
    def change_val():
        if var.get():
            user_data['debug']['enabled'] = True
        else:
            user_data['debug']['enabled'] = False

    var = BooleanVar(root, value=user_data['debug']['enabled'])
    dbg_check = Checkbutton(settings_data_frame, text='debug', command=change_val, variable=var)
    dbg_check.pack()

    if debug:
        def show_errors():
            w = show('errors')
            errs = Listbox(w)
            errs.pack(fill='both', expand=True)
            print('111111111111')
            for i in sys.stdout.read().split('\n'):
                if '[!!]' in i:
                    errs.insert('end', f'ERROR: {i}')

                elif '[!]' in i:
                    errs.insert('end', f'WARN: {i}')
            print('111111111111')


        Button(settings_data_frame, text='[debug] restart terminal', command=lambda: threading.Thread(target=terminal_thread, daemon=True).start()).pack()
        Button(settings_data_frame, text='errors', command=show_errors).pack()


def show(title='pop'):
    global locale, th
    settings_frame = Frame(highlightthickness=2, highlightcolor=th.fg)
    Button(settings_frame, text='X', command=settings_frame.destroy).pack(anchor='ne')
    Label(settings_frame, text=title).place(x=0, y=0)
    settings_data_frame = Frame(settings_frame, highlightthickness=2, highlightcolor=th.fg, width=300, height=300)
    settings_data_frame.pack_propagate(False)

    settings_data_frame.pack(fill='both', expand=True)
    settings_frame.place(relx=0.5, rely=0.5, anchor='center')

    return settings_data_frame


def find_chats():
    win = show('chat adding')
    win.pack_propagate(True)
    Label(win, text='Add Users').pack()
    contacts_select = ui.ListFrames(master=win)
    contacts_vars = {}
    def create():
        req = {'type': 'create_chat', 'users': [], 'is_public': is_public}
        for _contact_name, _contact in contacts_vars.items():
            if _contact.get():
                req['users'].append(_contact)

        if is_public:
            req['public_id'] = link_entry.get()

        print(req)

        print(client.communicate(req))


    for contact in user_data['contacts']:
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
        link_entry.pack_forget()

    def public_set():
        nonlocal is_public
        is_public = True
        public_var.set(True)
        private_var.set(False)
        link_lbl.pack(anchor='nw', side='left')
        link_entry.pack(anchor='nw', side='right')

    for_checks_fr = Frame(win)
    for_link_fr = Frame(win)
    link_entry = Entry(for_link_fr)
    link_lbl = Label(for_link_fr, text='Public link for you chat: ')
    is_public = False
    private_var = BooleanVar(value=not is_public)
    public_var = BooleanVar(value=is_public)
    private_check = Checkbutton(for_checks_fr, text='Private', variable=private_var, command=private_set)
    private_check.pack(anchor='nw', side='left')
    public_check = Checkbutton(for_checks_fr, text='Public', variable=public_var, command=public_set)
    public_check.pack(anchor='nw', side='right')
    for_checks_fr.pack()
    for_link_fr.pack()

    Button(win, text='Create', command=create).pack(fill='x', expand=True, side='bottom')


def build_ui():
    global message_entry, root_frame_for_chats, main_container, send_part, top_menu, main_menu_state_lbl
    if debug:
        root.config(bg='blue')
    print(f'[1] before ff {root.winfo_children()}')
    top_menu.destroy()

    top_menu = Frame(highlightcolor=th.fg, highlightthickness=2)
    main_menu_state_lbl = Label(top_menu, textvariable=main_menu_state_var)
    settings_butt = Button(top_menu, text=locale.get('base.settings', 'Settings'), command=settings)

    settings_butt.place(rely=1.0, relx=1.0, anchor='se', relheight=1.0)
    main_menu_state_lbl.pack(fill='y', expand=True)

    top_menu.pack(fill='x')

    find_chats_button = Button(root, text='//', command=find_chats)
    send_part.destroy()
    main_container.destroy()
    print(root.winfo_children())

    if chat == '':

        main_container = ui.ListFrames()
        main_container.pack(fill='both', expand=True)
        #main_container.for_w.pack_propagate(False)
        if debug:
            main_container.configure(bg='red')
            main_container.for_w.configure(bg='green')
            log = Label(root)
            log.place(x=0, rely=1.0, anchor='sw')

        #chat_selects = {}

        if chats != {}:
            for chat_name in chats.keys():
                w = Label(main_container.for_w, text=chat_name, highlightthickness=2)
                w.pack(pady=5, padx=5, fill='x', ipady=10)
                w.bind('<Button-1>', lambda e: load_chat(e.widget['text']))

                if debug:
                    log['text'] += chat_name +'\n'
            print(main_container.winfo_width(), main_container.canvas.winfo_width(), main_container.for_w.winfo_width())
        else:
            Label(main_container.for_w, text=locale.get('chat_menu.start_lbl', 'Create or find chats with "//" button')).pack(fill='both', expand=True)

        find_chats_button.place(relx=1.0, rely=1.0, anchor='se')
        find_chats_button.lift()
    else:
        send_part.destroy()
        main_container.destroy()
        main_menu_state_lbl.configure(textvariable=Variable(value=f'MSGR QWS / {chat}'))
        Button(top_menu, text='<--', command=lambda: load_chat('')).place(x=0, y=0, relheight=1.0)

        send_part = Frame(highlightthickness=2)
        message_entry = Text(send_part, autoseparators=True, height=1)
        message_entry.pack(fill='both', expand=True, side='left')
        def wrp():
            _msg = send_message()
            create_message(_msg)
        Button(send_part, text='^\n|', command=wrp).pack(fill='y', expand=True, side='left')

        main_container = ui.ListFrames()
        main_container.pack(fill='both', expand=True, anchor='nw')
        send_part.pack(side='bottom', fill='x')
        if debug:
            main_container.configure(bg='red', highlightthickness=5, highlightcolor='purple')
            main_container.canvas.configure(bg='yellow')
            main_container.for_w.configure(bg='green')
            log = Label(root)
            log.place(x=0, rely=1.0, anchor='sw')

       # chat_selects = {}

        def create_message(_msg):
            _w = Frame(main_container.for_w, highlightthickness=2, highlightcolor='white')
            Label(_w, text=_msg['from'], font=(th.font[0], int(th.font[1] - 1))).pack(anchor='nw')
            Label(_w, text=_msg['text'], justify='left').pack(side='left')
            Label(_w, text=_msg['time'], font=(th.font[0], int(th.font[1] - 1))).pack(anchor='se', side='left')
            if 'status' in _msg:
                print(_msg)
                err = Label(_w, text=_msg['status'])
                if _msg['status'] == '(!)':
                    err.config(fg='red')
                if 'status_full' not in _msg:
                    _msg['status_full'] = '(!) Unknown'
                err.status_full = _msg['status_full']
                err.pack(anchor='se', side='left')
                def show_err(event):
                    if not hasattr(err, 'popup'):
                        err.popup = None
                    if err.popup is None:
                        err.popup = Label(root, text=err.status_full, highlightthickness=2, justify='left')
                        err.popup.place(x=err.winfo_rootx() - err.winfo_toplevel().winfo_rootx(), y=err.winfo_rooty() - err.winfo_toplevel().winfo_rooty(), anchor='ne')
                        print(err.place_info())
                    else:
                        err.popup.destroy()
                        err.popup = None

                err.bind('<Enter>', show_err)
                err.bind('<Leave>', show_err)
            print(_msg)
            if _msg['from'] != 'You':
                _w.pack(pady=5, padx=5, anchor='w')
            else:
                _w.pack(pady=5, padx=5, anchor='e')

            if debug:
                log['text'] += str(_msg) + '\n'

        if chats[chat]:
            for msg in chats[chat]:
                create_message(msg)
            print(main_container.winfo_width(), main_container.canvas.winfo_width(), main_container.for_w.winfo_width())
        else:
            Label(main_container.for_w,
                  text=locale.get('chat.empty', 'No messages in this chat...')).pack(fill='both',expand=True)

    print(f'[1] after ff {root.winfo_children()}')


def load_chat(_chat):
    global chat
    print(f'[*] loading {_chat}')
    chat = _chat
    build_ui()


def send_message():
    msg = message_entry.get("0.0", 'end')
    if msg.strip() == "":
        return None

    try:
        client.send({'type': 'msg', 'to': f'{chats[chat]}', 'from': client.username, 'text': msg, 'time': time.strftime("%H:%M:%S")})
        adds = {}
    except Exception as _ex:
        _ex = str(_ex.__class__)
        print(traceback.format_exc())
        print(_ex)
        _ex_class = _ex[_ex.find("'") + 1:_ex.rfind("'")]
        adds = {'status_full': f'(!) {locale.get("chat.error_send", "Error sending message")}: {_ex_class}', 'status': '(!)'}
    message_entry.delete('0.0', END)
    return update_chat_log(msg, adds)


def update_chat_log(msg, additional=None):
    msg = {'from': 'You', 'text': msg, 'time': time.strftime("%H:%M:%S")}
    for key, val in additional.items():
        msg.update({key: val})
    chats[chat].append(msg)
    return msg


def update_menu_state():
    if main_menu_state_var.get() != main_menu_state:
        print(f'[*] updating main menu state to {main_menu_state}')
        main_menu_state_var.set(main_menu_state)


def backup_datas():
    chats.backup()
    user_data.backup()


def printin(s, h):
    h.write(f'{s}\n')


if __name__ == '__main__':

    class Log:
        def __init__(self, original):
            self.original = original
            self.buffer = StringIO()

        def write(self, dt):
            self.original.write(f'{dt}')
            self.buffer.write(f'{dt}\n')

        def read(self):
            self.buffer.seek(0)
            return self.buffer.read()

        def flush(self):
            pass

    sys.stdout = Log(sys.__stdout__)
    sys.stderr = Log(sys.__stderr__)
    def excepthook(x, y=None, z=None):
        printin(f'==== TRACEBACK {x} ====\n{''.join(traceback.format_exception(x, y, z))}==== END ====', sys.stderr)
    sys.excepthook = excepthook

    print('[*] MSGR-QWS, 2025')

    if platform.system() == 'Windows':
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception as _ctypes_error:
            print(f'[*] Failed to SetProcessDpiAwareness: {_ctypes_error}')

    chat = ''

    print('[*] * - info, ! - warning, !! - error')
    print('')

    print('[*] getting user data')
    user_data = utils.UserData(open('./data/user_data.json', 'r'))

    print('[*] checking keys')
    need_keys = ['theme', 'locale', 'username', 'password', 'addr', 'debug']
    for _key in need_keys:
        if _key not in user_data.keys():
            print(f'[*] setting default value for {_key}')
            user_data[_key] = ''
    print('[*] keys checked!')

    debug = user_data['debug']['enabled']
    debug_widgets = user_data['debug']['widgets']
    if debug == '':
        user_data['debug'] = {}
        debug = False

    print('[*] loading chat history')
    try:
        chats = utils.EncryptedUserData(open('./data/chat_history.json', 'r'))
    except Exception as _chat_hist_load_ex:
        print(f'[!!] chat history corrupt: {_chat_hist_load_ex}')
        jsoncrypt.dump({}, open('./data/chat_history_temp.json', 'w+'))
        chats = utils.EncryptedUserData(open('./data/chat_history_temp.json', 'r'))

    print('[*] loaded')

    root = Win()
    root.geometry('900x500')
    root.title('MSGR QWS')
    root.curr_container = None

    # global widgets
    message_entry = Text()
    root_frame_for_chats = Frame()
    main_container = Frame()
    send_part = Frame()
    top_menu = Frame()
    main_menu_state_lbl = Label()

    main_menu_state_var = StringVar(root)
    main_menu_state = 'MSGR QWS'

    print('[*] loading theme')
    th = utils.Theme(user_data['theme'])
    root.option_add('*Background', th.bg)
    root.option_add('*Foreground', th.fg)
    root.option_add('*Font', th.font)
    root.configure(bg=th.bg)

    print('[*] loading locale')
    locale = utils.Locale(user_data['locale'])
    print('[*] checking locale elements')
    ans = locale.get('m_lbl.program_title', 'MSGR QWS')
    #if 'locale_key' in dir(ans):
    #    print(f'[*] good localization (key: {ans.locale_key})')
    #    print('[*] checking with widgets')
    #    lbl = Label(text=locale.get('m_lbl.program_title', 'MSGR QWS'))
    #    try:
    #        print(f'[*] widget result: {lbl["text"].locale_key}')
    #    except AttributeError:
    #        print(f'[!] failed to get widget result: text hasn't locale_key attr: {lbl["text"].__class__}')
#
    #else:
    #    print(f'[!] Failed to check locale for _LocaleElem class:\n{dir(ans)}')

    print('[*] connecting to server')
    if user_data['addr'] == '':
        print('[*] getting addr from git')
        tmp = requests.get("https://raw.githubusercontent.com/zcveo5/sturdy-octo-rotary-phone/main/addr.txt").text.split('\n')[0].split(':')
        user_data['addr'] = [tmp[0], int(tmp[1])]

    client = com.Server(user_data['addr'][0], user_data['addr'][1], user_data['username'], user_data['password'])

    root.update()

    if user_data['username'] == '' or user_data['password'] == '':
        def confirm():
            user_data['username'] = user_entry.get()
            user_data['password'] = pass_entry.get()
            root.quit()

        server_popup = show()
        user_entry = Entry(server_popup)
        user_entry.pack()
        pass_entry = Entry(server_popup)
        pass_entry.pack()
        Button(server_popup, text=locale.get('base.confirm', 'Confirm'), command=confirm).pack()
        root.mainloop()

    def start_server_th():
        global main_menu_state
        main_menu_state = locale.get('m_lbl.connecting_state', 'Connecting')
        try:
            client.connect()
        except ConnectionError:
            if debug:
                printin(f'[debug] Error connecting to server:\n{traceback.format_exc()}', sys.__stderr__)
            main_menu_state = locale.get('m_lbl.failed_to_connect_state', 'Failed to connect')
            time.sleep(2)
        main_menu_state = locale.get('m_lbl.program_title', 'MSGR QWS')

    if debug:
        def terminal_thread():
            def execute():
                exec(command.get("0.0", "end"), globals(), locals())

            ter = Toplevel(root)
            ter.title('terminal')
            command = Text(ter)
            Button(ter, text='exec', command=execute).pack()
            command.pack()


        threading.Thread(target=terminal_thread, daemon=True).start()

    threading.Thread(target=start_server_th, daemon=True).start()

    root.after(250, print, "[*] starting loops")

    root.create_loop(update_menu_state, 250)
    root.create_loop(backup_datas, 5000)

    build_ui()
    root.mainloop()

    print('[*] exiting')
    user_data.backup()
    chats.backup()
    print('[*] bye')
else:
    print(__name__)
    print('not main, skip')