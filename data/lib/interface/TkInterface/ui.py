"""интерфейс"""

import tkinter
from tkinter import TclError
from typing import Literal
from data.lib.printlib import print_adv

popups = []
def lift_popups():
    for i in popups:
        try:
            i.lift()
        except TclError:
            pass


def _get_default_th():
    _s = tkinter.Label()
    return _s['bg'], _s['fg'], _s['font']


def configure_children_static(master, **cnf):
    def recursive_configure(widget):
        for _cfg_key, _cfg_val in cnf.items():
            try:
                widget.configure({_cfg_key: _cfg_val})
            except tkinter.TclError:
                pass

        if hasattr(widget, 'winfo_children'):
            for child in widget.winfo_children():
                recursive_configure(child)

    for cfg_key, cfg_val in cnf.items():
        try:
            master.configure({cfg_key: cfg_val})
        except tkinter.TclError:
            pass

    for _child in master.winfo_children():
        recursive_configure(_child)


class _Misc(tkinter.Misc):
    """Additions to tkinter's Misc"""
    def destroy_children(self):
        for _child in self.winfo_children():
            _child.destroy()

    def configure_children(self, **kwargs):
        def recursive_configure(widget):
            for _cfg_key, _cfg_val in kwargs.items():
                try:
                    widget.configure({_cfg_key: _cfg_val})
                except tkinter.TclError:
                    pass

            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    recursive_configure(child)

        for _child in self.winfo_children():
            recursive_configure(_child)

    def create_loop(self, target, ms=100, *_args):
        def _loop_wrp(*args):
            _r = target()
            if _r != -1:
                self.after(ms, _loop_wrp, args)

        self.after(ms, _loop_wrp, *_args)

    def mainloop(self, n = 0):
        try:
            super().mainloop(n)
        except Exception as _main_lp_ex:
            print_adv(f'[!!] {self} mainloop failed {_main_lp_ex.__class__} {_main_lp_ex}')


class Win(tkinter.Tk, _Misc):
    """Tk with _Misc"""
    pass


class Toplevel(tkinter.Toplevel, _Misc):
    pass


class Frame(tkinter.Frame, _Misc):
    pass


# Widgets

class ArrowButton:
    def __init__(self, master, command=None, text=''):
        self.bg = _get_default_th()[0]
        self.fg = _get_default_th()[1]
        self.font = _get_default_th()[2]
        self.master = master
        def pressed(event):
            _txt['bg'] = 'white'
            _arrow['bg'] = 'white'
            event.widget['bg'] = 'white'
            _txt['fg'] = self.bg
            _arrow['fg'] = self.bg

        self.root_frame = tkinter.Frame(self.master, relief='raised', bg=self.bg, borderwidth=1)
        self.root_frame.bind('<Button-1>', pressed)
        def release(event):
            event.widget['bg'] = self.bg
            _txt['bg'] = self.bg
            _arrow['bg'] = self.bg
            _txt['fg'] = self.fg
            _arrow['fg'] = self.fg
            if callable(command):
                command()
        self.root_frame.bind('<ButtonRelease-1>', release)
        _txt = tkinter.Label(master=self.root_frame, text=text, bg=self.bg, fg=self.fg, font=self.font,)
        _txt.pack(anchor='w', fill='y', side='left')
        _arrow = tkinter.Label(master=self.root_frame, text='>', bg=self.bg, fg=self.fg, font=self.font)
        _arrow.pack(anchor='e', fill='y', side='right')

    def pack(self, **kwargs):
        self.root_frame.pack(**kwargs)


class Switch:
    def __init__(self, master, command=None, variable=None, text='', size=0.5):
        self.bg = _get_default_th()[0]
        self.fg = _get_default_th()[1]
        self.font = _get_default_th()[2]
        self.master = master
        self._status = False

        def pressed(event):
            if callable(command):
                command()
            if self._status:
                self._status = False
            else:
                self._status = True
            print(f'setting {self._status}')
            self.set(self._status)


        self.root_frame = tkinter.Frame(self.master, relief='raised', bg=self.bg, borderwidth=1)
        self.root_frame.bind('<Button-1>', pressed)
        self._switcher = tkinter.Frame(self.root_frame, highlightthickness=1, highlightcolor=self.fg, highlightbackground=self.fg)
        self._switcher.pack(fill='y',pady=5, padx=5, side='right')
        self.r_part = tkinter.Label(self._switcher, bg=self.fg, height=size, width=size * 2)
        self.r_part.pack(side='right')
        self.l_part = tkinter.Label(self._switcher, bg=self.bg, height=size, width=size * 2)
        self.l_part.pack(side='left')
        tkinter.Label(self.root_frame, text=text, bg=self.bg, fg=self.fg, font=self.font).pack(side='left')
        self.set(self._status)

    def set(self, s: bool):
        if s:
            self.r_part['bg'] = self.fg
            self.l_part['bg'] = self.bg
        else:
            self.r_part['bg'] = self.bg
            self.l_part['bg'] = self.fg


class Combobox:
    def __init__(self, master=None, bg=None, fg=None, font=None, values=None, _values=None, state='readonly', debug=False, **kw):
        self.parent = master
        if _values is not None:
            values = _values
        if values is None:
            values = []
        self.values = values
        self.var = tkinter.StringVar()
        self.bg = bg
        self.fg = fg
        self.font = font
        self._root_frame = tkinter.Frame(master, **kw)
        self._root_frame.pack_propagate(True)

        if bg is None:
            bg = tkinter.Label()["background"]  # Берем значение по умолчанию
        if fg is None:
            fg = tkinter.Label()["foreground"]
        if font is None:
            font = tkinter.Label()["font"]

        print_adv(f'[combobox {str(values)[0:10]}...] style: {bg} {fg} {font}')

        self.entry = tkinter.Entry(self._root_frame, textvariable=self.var, disabledbackground=bg, disabledforeground=fg, readonlybackground=bg)
        def wrp(event):
            self.entry.configure(readonlybackground=self.entry['bg'], disabledbackground=self.entry['bg'])
        self.entry.bind('<Configure>', wrp)
        self.entry.pack(fill='both', expand=True, side='left')
        self.btn = tkinter.Button(self._root_frame, text="▼", command=self.toggle_listbox)
        self.btn.pack(fill='both', expand=True, side='right')
        self.listbox = tkinter.Listbox(bg="white")

        if bg is not None:
            self._root_frame.configure(bg=bg)
            self.entry.configure(bg=bg)
            self.btn.configure(bg=bg)
            self.listbox.configure(bg=bg)
        if fg is not None:
            self.entry.configure(fg=fg)
            self.btn.configure(fg=fg)
            self.listbox.configure(fg=fg)
        if font is not None:
            self.entry.configure(font=font)
            self.btn.configure(font=font)
            self.listbox.configure(font=font)

        self.entry.update()

        print_adv(f'[combobox {str(values)[0:20]}...] style_exits_entry: {self.entry["bg"]} {self.entry["fg"]} {self.entry["font"]}')

        for value in values:
            self.listbox.insert('end', value)

        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self._root_frame.bind('<Unmap>', lambda e: self.pack_forget())
        def remap_lbox():
            print()
            if self.listbox.winfo_ismapped():
                self.listbox.place(x=self.entry.winfo_rootx() - self.entry.winfo_toplevel().winfo_rootx(),
                                   y=self.entry.winfo_rooty() - self.entry.winfo_toplevel().winfo_rooty() + self.entry.winfo_height(),
                                   anchor='nw',
                                   width=self.entry.winfo_width() + self.btn.winfo_width())
                print_adv(self.entry.winfo_rootx(), self.entry.winfo_rooty())
                self.listbox.lift()
        self.entry.bind("<KeyRelease>", self.filter_values)
        self.entry.bind("<Down>", lambda e: self.show_listbox())

        if debug:
            d = Win()
            statuses = tkinter.Label(d)
            statuses.pack()

            def upd_status():
                statuses['text'] = f'IsmappedRframe:{self._root_frame.winfo_ismapped()}\nIsmappedListboxSel:{self.listbox.winfo_ismapped()}'

            d.create_loop(upd_status)

    def set(self, _s):
        self.var.set(_s)

    def build(self, mode: Literal['place', 'pack', 'grid'], **kw):
        if mode == 'place':
            self._root_frame.place(**kw)
        elif mode == 'pack':
            self._root_frame.pack(**kw)
        else:
            self._root_frame.grid(**kw)

    def toggle_listbox(self):
        if self.listbox.winfo_ismapped():
            print_adv('hide')
            self.hide_listbox()
        else:
            print_adv('show')
            self.show_listbox()

    def show_listbox(self):
        self.listbox.place(x=self.entry.winfo_rootx() - self.entry.winfo_toplevel().winfo_rootx(),
                           y=self.entry.winfo_rooty() - self.entry.winfo_toplevel().winfo_rooty() + self.entry.winfo_height(),
                           anchor='nw',
                           width=self.entry.winfo_width() + self.btn.winfo_width())
        print_adv(self.entry.winfo_rootx(), self.entry.winfo_rooty())
        self.listbox.lift()
        self.listbox.focus_set()

    def hide_listbox(self):
        self.listbox.place_forget()
        self.entry.focus_set()

    def on_select(self, event):
        if self.listbox.curselection():
            index = self.listbox.curselection()[0]
            value = self.listbox.get(index)
            self.var.set(value)
        self.hide_listbox()

    def filter_values(self, event):
        pattern = self.var.get().lower()
        self.listbox.delete(0, 'end')
        for value in self.values:
            if pattern in value.lower():
                self.listbox.insert('end', value)

    def get(self, *args):
        return self.var.get()

    def bind(self, _p, _a):
        if _p == '<<ComboboxSelected>>':
            def wrapper(event):
                self.on_select(event)
                class _Obj:
                    pass
                event.widget = _Obj()
                event.widget.get = self.get
                _a(event)
            print_adv(f'binding {_p} to P{_a}')
            self.listbox.bind('<<ListboxSelect>>', wrapper)

    def pack(self, **kw):
        self.build('pack', **kw)

    def destroy(self):
        self._root_frame.destroy()
        self.listbox.destroy()

    def pack_forget(self):
        self._root_frame.pack_forget()
        self.listbox.place_forget()

    def place_forget(self):
        self._root_frame.place_forget()
        self.listbox.place_forget()

    def grid_forget(self):
        self._root_frame.grid_forget()
        self.listbox.place_forget()


class ListFrames(tkinter.Frame, _Misc):
    """scrollable space"""

    def __init__(self, **kwargs):
        # scheme:
        # root_frame -> canvas -> scrollable_frame
        root_frame = tkinter.Frame(**kwargs)
        self._dest = False
        canvas = tkinter.Canvas(root_frame, highlightthickness=0)

        super().__init__(canvas)

        self.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=self, anchor="nw")

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)

        canvas.pack(side="left", fill="both", expand=True)

        def scroll(event):
            scroll_speed = 5

            if event.delta > 0:
                canvas.yview_moveto(max(0.0, canvas.yview()[0] - scroll_speed * 0.01))
            else:
                canvas.yview_moveto(min(1.0, (canvas.yview()[0] + scroll_speed * 0.01)))

        canvas.bind_all("<MouseWheel>", scroll)

        self.canvas = canvas
        self.root_frame = root_frame
        self.for_w = self

    def scroll_to_bottom(self):
        """Прокручивает область просмотра до самого низа"""
        self.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.for_w.event_generate("<Configure>")
        self.canvas.yview_moveto(1.0)  # 1.0 означает 100% прокрутки вниз
        self.canvas.update_idletasks()  # Обновляем отображение

    def pack(self, **kw):
        self.root_frame.pack(**kw)

    def place(self, **kw):
        self.root_frame.place(**kw)

    def pack_forget(self, **kw):
        self.root_frame.pack_forget()

    def destroy(self):
        def recurse_destroy(master, level):
            for c in master.children.copy().values():
                if c != self.root_frame:
                    recurse_destroy(c, level+1)
                    c.destroy()
        recurse_destroy(self, 1)
        r_frame_back = self.root_frame
        self.root_frame = None
        # self.destroy()
        if r_frame_back is not None:
            r_frame_back.destroy()


class Popup(tkinter.Frame, _Misc):
    """Like-window widget in window"""
    def __init__(self, master: Win | tkinter.Tk = None, size=None,
                 style=None, title: str = 'Popup', map_on_init=True):
        # if master is None:
        #    raise TypeError(f'Master win is not provided: {app_root_window}')
        if size is None:
            size = [300, 300]
        self.style = style
        self.size = size

        if style is None:
            style = [tkinter.Label()['bg'], tkinter.Label()['fg'], tkinter.Label()['font']]

        self.root_frame = tkinter.Frame(master, width=size[0], height=size[1], highlightthickness=2)
        self.root_frame.pack_propagate(True)

        self.title_bar = tkinter.Frame(self.root_frame)
        self.title_bar.pack(fill='x')

        _batons = tkinter.Frame(self.title_bar)
        _batons.pack(anchor='ne', side='right')

        self.close_btn = tkinter.Button(_batons, text='X', command=self.root_frame.place_forget)
        self.close_btn.pack(anchor='ne', side='right')
        def toggle_mapped():
            if self.winfo_ismapped():
                self.pack_forget()
            else:
                self.pack(fill='both', expand=True)
        self.minimize_btn = tkinter.Button(_batons, text='-', command=toggle_mapped)
        self.minimize_btn.pack(anchor='ne', side='right')
        self.title_lbl = tkinter.Label(self.title_bar, text=title)
        self.title_lbl.pack(side='left')

        super().__init__(self.root_frame, width=size[0], height=size[1], highlightthickness=2)
        self._orig_propagate = self.pack_propagate
        self.pack_propagate = self._pack_propagate
        #self.pack_propagate(True)

        if style is not None:
            self.configure(bg=style[0], highlightcolor=style[1])
            self.root_frame.configure(bg=style[0], highlightcolor=style[1])
            self.close_btn.configure(bg=style[0], fg=style[1], font=style[2])
            self.title_lbl.configure(bg=style[0], fg=style[1], font=style[2])

        self.title_bar.bind('<Button-1>', self._start_move)
        self.title_bar.bind('<B1-Motion>', self._move)

        self._start_x = 0
        self._start_y = 0

        popups.append(self)

        if map_on_init:
            self.root_frame.place(x=0, y=0)
            self.pack()

    def _pack_propagate(self, state, force=False):
        if force:
            self._orig_propagate(state)

    def destroy(self):
        self.root_frame.place_forget()

    def update_idletasks(self):
        super().update_idletasks()
        self.root_frame.update_idletasks()
        self.size = [self.root_frame.winfo_width(), self.root_frame.winfo_height()]
        print_adv(self.size)

    def lift(self):
        self.root_frame.lift()

    def _start_move(self, event=None):
        self.root_frame.lift()
        if hasattr(event, 'x') and hasattr(event, 'y'):
            self._start_x = event.x
            self._start_y = event.y

    def _move(self, event):
        x = self.root_frame.winfo_x() + (event.x - self._start_x) // 2 * 2
        y = self.root_frame.winfo_y() + (event.y - self._start_y) // 2 * 2
        # self.title_lbl['text'] = f'{self.root_frame.winfo_x()}/{self.root_frame.master.winfo_width() - self.root_frame.winfo_width()} {self.root_frame.winfo_y()}/{self.root_frame.master.winfo_height() - self.root_frame.winfo_height()}'
        if 0 <= x <= self.root_frame.master.winfo_width() - self.root_frame.winfo_width():
            self.root_frame.place(x=x)
        if 0 <= y <= self.root_frame.master.winfo_height() - self.root_frame.winfo_height():
            self.root_frame.place(y=y)

    def update_info(self):
        self._start_x = 0
        self._start_y = 0
        self.update_idletasks()

    def resizable(self, x, y):
        if x or y:
            self.pack_propagate(True)
        else:
            self.pack_propagate(True)

    def title(self, t):
        self.title_lbl['text'] = t

    def protocol(self, prot, callback):
        if prot == 'WM_DELETE_WINDOW':
            self.close_btn['command'] = callback
