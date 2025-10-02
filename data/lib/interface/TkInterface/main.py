import sys, os
from tkinter import *
from data.lib import utils
from typing import Any
sys.path.append('./data/lib/interface/TkInterface')
import ui

_gvar = lambda n: Any
_svar = lambda n, v: None

def gvar(__name):
    return _gvar(__name)

def svar(__name, __value):
    _svar(__name, __value)

def update_var(__svar, __gvar):
    global _gvar, _svar
    _gvar, _svar = __gvar, __svar


class _ChatManage:
    def __init__(self, chat_name: str, actions, funcs, show, chat_data):
        self.chat_back = chat_name
        try:
            self.available_actions = actions
        except TypeError:
            self.available_actions = {}
        gvar('print_adv')('[ChatManage] Loading profile...', h=gvar('ui_log'))
        
        self.chat_data = chat_data
        self.funcs = funcs
        self.show = show
        self.profile()

    def manage_user(self, _e):
        show = self.show

        def delete():
            self.funcs[0](_e.widget.username, self.chat_data['link'])

        def make_admin():
            self.funcs[1](_e.widget.username, self.chat_data['link'])

        def remove_admin():
            self.funcs[2](_e.widget.username, self.chat_data['link'])

        _manage_user = show(f'manage panel for {_e.widget.username}')
        _manage_user.pack_propagate(False)
        Label(_manage_user, text=_e.widget.username).pack(anchor='w')
        Button(_manage_user, text='delete', command=delete).pack(anchor='nw')
        if _e.widget.username in self.chat_data['admins'] and gvar('user_data')['username'] in self.chat_data[
            'admins']:
            Button(_manage_user, text='remove admin', command=remove_admin).pack(anchor='nw')
        elif gvar('user_data')['username'] in self.chat_data['admins']:
            Button(_manage_user, text='make admin', command=make_admin).pack(anchor='nw')

    def exec_action(self, event):
        chat_back = self.chat_back

        gvar('print_adv')(f'chat menu action: {event.widget.action_name}', h=gvar('ui_log'))
        if event.widget.action_name == 'invite_users':
            self.add_user()
        elif event.widget.action_name == 'manage_users':
            _manage_w = self.show(f'manage users "{chat_back}"')
            _manage_w.pack_propagate(False)
            for _user in self.chat_data['users']:
                _btn = Button(_manage_w, text=_user)
                _btn.username = _user
                _btn.bind('<Button-1>', self.manage_user)
                _btn.pack(anchor='nw')

    def add_user(self):
        chat_back = self.chat_back

        def add():
            _invite_w.destroy()
            # req = {'c': [], 'type': 'add_users', 'chat': self.chat_data['link']}
            u = []
            for _name, _value in contacts_vars.items():
                if _value.get():
                    u.append(_name)
            self.funcs[3](self.chat_data['link'], *u)

        _invite_w = self.show(f'Invite into {chat_back}')
        Label(_invite_w, text='Add Users').pack()
        contacts_select = ui.ListFrames(master=_invite_w)
        contacts_vars = {}

        for contact in self.funcs[4]():
            contacts_vars[contact] = BooleanVar(master=_invite_w, value=False)
            _chb = Checkbutton(contacts_select.for_w, text=contact, variable=contacts_vars[contact])
            _chb.pack(anchor='nw')

        contacts_select.pack()
        Button(_invite_w, text='add', command=add).pack()

    def chat_menu(self):
        chat_back = self.chat_back
        _w = self.show(f'Chat manage: {chat_back}')
        available_actions = self.available_actions

        if gvar('debug'):
            Label(_w, text='Available actions:\n' + '\n'.join(available_actions), justify='left').pack(anchor='nw')
        _actions = ui.ListFrames(master=_w)

        for i in available_actions:
            _a = Button(_actions.for_w, text=i)
            _a.action_name = i
            _a.bind('<Button-1>', self.exec_action)
            _a.pack(anchor='nw')
        _actions.pack()

    def profile(self):
        _w = self.show(f'Profile {self.chat_back}')
        _w.pack_propagate(True)
        Label(_w, text=self.chat_back).pack()
        _users_w = ui.ListFrames(master=_w, highlightthickness=1)
        _users_w.pack(fill='both', expand=True)
        _users_w = _users_w.for_w
        if gvar('debug'):
            Label(_users_w, text='Test').pack()
        for _user in self.chat_data['users']:
            gvar('print_adv')(f'[ChatManage--{self.chat_back}] {_user}', h=gvar('ui_log'))
            _btn = Button(_users_w, text=_user)
            if _user in self.chat_data['admins']:
                _btn['text'] += ' | Admin'
            if _user == gvar('client').username:
                _btn['text'] += ' | You'
            _btn.username = _user
            _btn.bind('<Button-1>', self.manage_user)
            _btn.pack(anchor='nw', fill='x', padx=10, pady=2)
            gvar('print_adv')(
                f'[ChatManage--{self.chat_back}] IsMapped:{_btn.winfo_ismapped()} Exists:{_btn.winfo_exists()}', h=gvar('ui_log'))
        if self.available_actions != ['invite_users']:
            Button(_w, text='Manage chat', command=self.chat_menu).pack(fill='x', side='bottom')
        Button(_w, text='Add user', command=self.add_user).pack(fill='x', side='bottom')
        gvar('print_adv')('[ChatManage] ready', h=gvar('ui_log'))


class Interface:
    class MessageBubble(Frame):
        for_w: Frame
        err_status: Label

        def __init__(self, master=None, **kwargs):
            super().__init__(master, **kwargs)
            self.configure(
                highlightcolor=gvar('th').fg,
                highlightbackground=gvar('th').fg
            )

    def __init__(self, _base_chats_get_func, _base_chat_manage_cfg):

        self.type = 'TKINTER'

        self.root = ui.Win()
        self.root.geometry('900x500')
        self.root.title('MSGR QWS')
        self.root.curr_container = None

        self._b_ui_cfg = [_base_chats_get_func, _base_chat_manage_cfg]
        self._bubbles_cfg = {}

        self.main_menu_state_var = StringVar(self.root, value='TkInterface')
        self.top_menu: Frame = Frame(self.root)
        self.top_menu.init_completed = False
        self.main_container: ui.ListFrames = ui.ListFrames()
        self.send_part: Frame = Frame()
        self.message_entry = Text()

    def create_loop(self, target, ms):
        self.root.create_loop(target, ms)

    def destroy(self):
        try:
            self.root.destroy()
        except TclError:
            pass

    def serv_select(self, cmd):
        def _confirm():
            cmd(user_entry.get(), pass_entry.get())
            server_popup.destroy()
            self.root.quit()

        server_popup = self.show('Server select')
        user_entry = Entry(server_popup)
        user_entry.pack()
        pass_entry = Entry(server_popup)
        pass_entry.pack()
        Button(server_popup, text=gvar('locale').get('base.confirm', 'Confirm'), command=_confirm).pack()
        self.root.mainloop()

        server_popup.destroy()
        self.root.quit()

    def loading_lbl_interface(self):
        self.root.update()
        Label(self.root, text='Loading...').place(x=0, y=0)

    def start(self):
        self.update()
        try:
            self.build_ui(force_top_menu_recreate=True)
            self.root.create_loop(self.update_menu_state, 500)
        except Exception as e:
            gvar('print_adv')(f'[Interface] FAILED TO START INTERFACE: {e}', h=sys.stderr)
            #showerror('Error starting interface', traceback.format_exc())
        self.root.mainloop()

    def show(self, title):
        _root = ui.Popup(master=self.root, title=title)
        return _root

    def settings(self, lc_func, th_func, set_var_debug, set_var_debug_widgets):
        def th_update(event):
            th_func(event.widget.get())

        def lc_update(event):
            lc_func(event.widget.get())

        def change_val():
            set_var_debug(var.get())

        def change_val_widget():
            set_var_debug_widgets(var_widget.get())

        settings_data_frame = self.show(gvar('locale').get('base.settings', 'Settings'))
        settings_data_frame.root_frame.place_forget()
        settings_data_frame.root_frame.place(x=0, y=0, anchor='nw', relheight=1.0)

        lc = ui.Combobox(settings_data_frame, values=os.listdir('./data/locale'))
        lc.set(gvar('locale').get('settings.locale_txt', 'Localization'))
        lc.bind('<<ComboboxSelected>>', lc_update)
        lc.entry.configure(state='readonly')
        lc.pack(fill='x')

        th_box = ui.Combobox(settings_data_frame, values=os.listdir('./data/theme'))
        th_box.set(gvar('locale').get('settings.theme_txt', 'Theme'))
        th_box.bind('<<ComboboxSelected>>', th_update)
        th_box.entry.configure(state='readonly')
        th_box.pack(fill='x')

        var = BooleanVar(self.root, value=gvar('user_data')['debug']['enabled'])
        dbg_check = Checkbutton(settings_data_frame, text='debug', command=change_val, variable=var)
        dbg_check.pack(fill='x')

        var_widget = BooleanVar(self.root, value=gvar('user_data')['debug']['widgets'])
        wid_dbg_check = Checkbutton(settings_data_frame, text='dbg widgets', command=change_val_widget,
                                    variable=var_widget)
        wid_dbg_check.pack(fill='x')

    def showinfo(self, title, text):
        _r = self.show(title)
        Label(_r, text=text, justify='left').pack(anchor='nw')
        return _r

    def create_chat(self, create_func, contacts):
        win = self.show('chat adding')
        win.pack_propagate(True)
        Label(win, text='Add Users').pack()
        contacts_select = ui.ListFrames(master=win)
        contacts_vars = {}

        for contact in contacts:
            contacts_vars[contact] = BooleanVar(master=win, value=False)
            w = Checkbutton(contacts_select.for_w, text=contact, variable=contacts_vars[contact])
            w.pack(anchor='nw')

        contacts_select.pack()
        Label(win, text='Link type').pack()

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

        Button(win, text='Create',
               command=lambda: create_func(is_public, contacts_vars, link_entry.get(), name_entry.get())).pack(fill='x',
                                                                                                               expand=True,
                                                                                                               side='bottom')

    def create_message(self, _msg):
        main_cont = self.main_container
        gvar('print_adv')(f'[CM] creating {_msg} at {main_cont}', h=gvar('ui_log'))
        try:
            _w = self.MessageBubble(main_cont.for_w, highlightthickness=2)
        except Exception as _w_create_err:
            self.showinfo('Error', f'Failed to create message bubble: {_w_create_err}')
            return None
        Label(_w, text=_msg['from'], font=(gvar('th').font[0], int(gvar('th').font[1] - 1))).pack(anchor='nw')
        Label(_w, text=_msg['text'], justify='left').pack(side='left')
        Label(_w, text=_msg['time'], font=(gvar('th').font[0], int(gvar('th').font[1] - 1))).pack(anchor='se', side='left')
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
                    err.popup = Label(self.root, text=err.status_full, highlightthickness=2, justify='left')
                    err.popup.place(x=err.winfo_rootx() - err.winfo_toplevel().winfo_rootx(),
                                    y=err.winfo_rooty() - err.winfo_toplevel().winfo_rooty(), anchor='ne')
                else:
                    err.popup.destroy()
                    err.popup = None

            err.bind('<Enter>', show_err)
            err.bind('<Leave>', show_err)
            _w.err_status = err
        if _msg['from'] not in [gvar('user_data')['username'], 'You']:
            _w.pack(pady=5, padx=5, anchor='w')
        else:
            _w.pack(pady=5, padx=5, anchor='e')
        _id = utils.randgen(10)
        self._bubbles_cfg[_id] = _w
        return _id

    def cfg_msg_bubble(self, _msg, _id):
        _w = self._bubbles_cfg.get(_id, None)
        gvar('print_adv')(f'configure {_id} ({self._bubbles_cfg[_id]}) - {_msg}', h=gvar('ui_log'))
        if _w is None:
            raise KeyError(f'Unknown _bubble_cfg key: {_id}')
        for k, v in _msg.items():
            if k == 'status':
                _w.err_status['text'] = v
            elif k == 'status_full':
                _w.err_status.status_full = v
            elif k == 'set_status_state_err':
                _w.err_status['bg'] = 'red'
            else:
                gvar('print_adv')(f'[sERR-Wrp-{gvar('ui_log').name}][CFG Into {_id}] - error: unknown key: {k}', h=sys.stderr)
        _w.update()

    def search(self, _chats, _join, _add_to_c):
        _search_pop = self.show(gvar('locale').get('base.search', 'Search'))
        _search_pop.pack_propagate(False)
        _chat_list = ui.ListFrames(master=_search_pop)
        _chat_list.pack(fill='both', expand=True)
        try:
            s = _chats
        except OSError:
            s = {'h': ['Unable to get chat list']}
        print(f'all public chats {s}')

        def show_user_profile(e):
            prof = ui.Popup(title=f'User: {e.widget["text"]}')
            prof.pack_propagate(False)
            Label(prof, text=e.widget['text']).pack(anchor='nw')
            Button(prof, text='add to contacts',
                   command=_add_to_c).pack(side='bottom')

        def show_chat_profile(e):
            prof = ui.Popup(title=f'Chat: {e.widget["text"]}')
            prof.pack_propagate(False)
            Label(prof, text=e.widget['text']).pack(anchor='nw')
            if gvar('debug'):
                chat_inf = ''
                for _i in e.widget.chat_data:
                    chat_inf += f'{_i}: {e.widget.chat_data[_i]}\n'
                Label(prof, text=f'chat info: {chat_inf}').pack(anchor='nw')
            Button(prof, text='join',
                   command=_join).pack(side='bottom')

        for i in s['h']:
            if isinstance(i, str):
                _w = Label(_chat_list, text=str(i), highlightthickness=1)
                _w.bind('<Button-1>', show_user_profile)
                _w.pack(anchor='nw', fill='x')
            elif isinstance(i, dict):
                _w = Label(_chat_list, text=str(i['name']), highlightthickness=1)
                _w.chat_data = i.copy()
                _w.bind('<Button-1>', show_chat_profile)
                _w.pack(anchor='nw', fill='x')

    def build_ui(self, force_top_menu_recreate=False):
        """собирает и обновляет основной пользовательский интерфейс.

            В зависимости от текущего состояния (выбран чат или нет) отображает:
            - список чатов
            - окно сообщений выбранного чата
            - панель ввода сообщений
            """

        _chats = self._b_ui_cfg[0]()
        _chat_manage_cfg = self._b_ui_cfg[1]
        if 'functions' in _chat_manage_cfg:
            _chat_manage_cfg['funcs'] = _chat_manage_cfg['functions']
        if 'funcs' not in _chat_manage_cfg or 'actions' not in _chat_manage_cfg:
            self.showinfo('Error', f'Invalid _chat_manage_cfg - {_chat_manage_cfg}')
        if gvar('debug_widgets'):
            self.root.config(bg='blue')
        _recreate_top_menu = False
        if hasattr(self.top_menu, 'init_completed'):
            _recreate_top_menu = True
        if force_top_menu_recreate:
            _recreate_top_menu = True

        try:
            self.top_menu.pack(fill='x')
            self.top_menu.pack_forget()
        except TclError:
            gvar('print_adv')('tcl in bui at test self.top_menu', h=gvar('ui_log'))
            _recreate_top_menu = True

        if _recreate_top_menu:
            gvar('print_adv')('recreate top menu', h=gvar('ui_log'))
            self.top_menu.destroy()

            self.top_menu = Frame(self.root, highlightthickness=2)
            main_menu_state_lbl = Label(self.top_menu, textvariable=self.main_menu_state_var)
            settings_butt = Button(self.top_menu, text=gvar('locale').get('base.settings', 'Settings'), command=gvar('settings'))

            search_button = Button(self.top_menu, text=gvar('locale').get('base.search', 'Search'), command=gvar('search'))
            search_button.place(rely=0, relx=0, anchor='nw', relheight=1.0)

            settings_butt.place(rely=1.0, relx=1.0, anchor='se', relheight=1.0)
            main_menu_state_lbl.pack(fill='y', expand=True)
        else:
            _th = Label()
            ui.configure_children_static(self.top_menu, bg=_th['bg'], fg=_th['fg'], font=_th['font'],
                                         highlightcolor=_th['fg'], highlightbackground=_th['fg'])

        find_chats_button = Button(self.root, text='//', command=gvar('create_chat'))

        self.send_part.destroy()
        self.main_container.destroy()

        if gvar('chat') == '' and gvar('chat_manage'):
            self.top_menu.pack(fill='x')
            self.main_container = ui.ListFrames()
            self.main_container.pack(fill='both', expand=True)
            # main_container.for_w.pack_propagate(False)
            if gvar('debug_widgets'):
                self.main_container.configure(bg='red')
                self.main_container.for_w.configure(bg='green')

            # chat_selects = {}

            if _chats != {}:
                for chat_name in _chats.keys():
                    w = Label(self.main_container.for_w, text=chat_name, highlightthickness=2)
                    w.pack(pady=5, padx=5, fill='x', ipady=10)
                    w.bind('<ButtonRelease-1>', lambda e: gvar('load_chat')(e.widget['text']))
            else:
                Label(self.main_container.for_w,
                      text=gvar('locale').get('chat_menu.start_lbl', 'Create chat with "//" button')).pack(fill='both',
                                                                                                   expand=True)

            find_chats_button.place(relx=1.0, rely=1.0, anchor='se')
            find_chats_button.lift()
        else:
            self.top_menu.pack_forget()
            self.send_part.destroy()
            self.main_container.destroy()
            top_menu_chat = Frame(highlightthickness=2)
            Label(top_menu_chat, text=gvar('chat')).pack(fill='y', expand=True)

            def back():
                top_menu_chat.pack_forget()
                svar('chat_manage', True)
                gvar('load_chat')('', True)

            Button(top_menu_chat, text='<--', command=back).place(x=0, y=0, relheight=1.0)
            try:
                (Button(top_menu_chat, text='Menu', command=lambda: _ChatManage(gvar('chat'),
                                                                                funcs=_chat_manage_cfg['funcs'],
                                                                                actions=_chat_manage_cfg['actions'](
                                                                                    str(gvar('chats')[gvar('chat')]['link'])),
                                                                                show=self.show, chat_data=gvar('chats')[gvar('chat')].copy()))
                 .place(relx=1.0, y=0, relheight=1.0, anchor='ne'))
            except TclError:
                pass
            top_menu_chat.pack(fill='x')

            self.send_part = Frame(highlightthickness=2)
            self.message_entry = Text(self.send_part, autoseparators=True, height=1)
            self.message_entry.pack(fill='both', expand=True, side='left')

            def wrp():
                _msg = gvar('send_message')()
                self.main_container.scroll_to_bottom()

            Button(self.send_part, text='^\n|', command=wrp).pack(fill='y', expand=True, side='right')

            self.main_container = ui.ListFrames()
            self.main_container.pack(fill='both', expand=True, anchor='nw')
            self.send_part.pack(side='bottom', fill='x')
            if gvar('debug_widgets'):
                self.main_container.configure(bg='red', highlightthickness=5)
                self.main_container.canvas.configure(bg='yellow')
                self.main_container.for_w.configure(bg='green')

            # chat_selects = {}

            if _chats[gvar('chat')]:
                for msg in _chats[gvar('chat')]['msgs']:
                    self.create_message(msg)
            else:
                Label(self.main_container.for_w,
                      text=gvar('locale').get('chat.empty', 'No messages in this chat...')).pack(fill='both', expand=True)

            self.main_container.scroll_to_bottom()

        ui.lift_popups()

    def update_menu_state(self):
        """обновляет состояние главного меню."""
        if self.main_menu_state_var.get() != gvar('main_menu_state'):
            gvar('print_adv')(f'[*] updating main menu state to {gvar('main_menu_state')}', h=gvar('ui_log'))
            self.main_menu_state_var.set(gvar('main_menu_state'))

    def get_msg(self):
        d = self.message_entry.get('0.0', 'end')
        self.message_entry.delete('0.0', 'end')
        return d

    def commit_theme(self, _th):
        root = self.root
        root.option_add('*highlightColor', _th.fg, 'widgetDefault')
        root.option_add('*highlightBackground', _th.fg)
        root.option_add('*readonlyBackground', _th.bg)
        root.option_add('*Background', _th.bg, 'widgetDefault')
        root.option_add('*Foreground', _th.fg, 'widgetDefault')
        root.option_add('*Font', _th.font, 'widgetDefault')
        root.configure(bg=_th.bg)
        root.configure_children(bg=_th.bg, fg=_th.fg, font=_th.font, highlightcolor=_th.fg, highlightbackground=_th.fg,
                                readonlybackground=_th.bg)

    def destroy_children(self):
        self.root.destroy_children()

    def update(self):
        try:
            self.root.update()
        except KeyboardInterrupt:
            pass

    def replace_chat_hist(self, _new):
        self._b_ui_cfg[0] = _new
