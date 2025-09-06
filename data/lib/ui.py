"""интерфейс"""

import tkinter
from tkinter import TclError
from typing import Literal

popups = []
def lift_popups():
    for i in popups:
        try:
            i.lift()
        except TclError:
            pass

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


class CustomWindow(tkinter.Tk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Убираем стандартный заголовок окна
        self.overrideredirect(True)

        # Настраиваем базовые параметры окна
        self.geometry("900x500")
        self.title("MSGR QWS")
        self.configure(bg="#2b2b2b")

        # Создаем кастомный заголовок
        self.title_bar = tkinter.Frame(self, bg="#2b2b2b", height=30, highlightthickness=1, highlightcolor="#444444")
        self.title_bar.pack(fill='x', side='top')
        self.title_bar.pack_propagate(False)

        # Заголовок окна
        self.title_label = tkinter.Label(
            self.title_bar,
            text="MSGR QWS",
            bg="#2b2b2b",
            fg="#ffffff",
            font=("Arial", 10)
        )
        self.title_label.pack(side='left', padx=10)

        # Кнопки управления окном
        button_frame = tkinter.Frame(self.title_bar, bg="#2b2b2b")
        button_frame.pack(side='right')

        # Кнопка свернуть
        self.minimize_btn = tkinter.Button(
            button_frame,
            text="─",
            bg="#2b2b2b",
            fg="#ffffff",
            bd=0,
            width=3,
            height=1,
            command=self.minimize_window,
            font=("Arial", 10)
        )
        self.minimize_btn.pack(side='right', padx=(0, 5))
        self.minimize_btn.bind("<Enter>", lambda e: self.minimize_btn.config(bg="#3a3a3a"))
        self.minimize_btn.bind("<Leave>", lambda e: self.minimize_btn.config(bg="#2b2b2b"))

        # Кнопка закрыть
        self.close_btn = tkinter.Button(
            button_frame,
            text="×",
            bg="#2b2b2b",
            fg="#ffffff",
            bd=0,
            width=3,
            height=1,
            command=self.quit_app,
            font=("Arial", 12)
        )
        self.close_btn.pack(side='right', padx=(0, 5))
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.config(bg="#e81123"))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.config(bg="#2b2b2b"))

        # Основная область содержимого
        self.content = tkinter.Frame(self, bg="#1e1e1e")
        self.content.pack(fill='both', expand=True)

        # Переменные для перемещения окна
        self._offset_x = 0
        self._offset_y = 0

        # Привязываем события для перемещения окна
        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<ButtonRelease-1>", self.stop_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)

        # Центрируем окно при запуске
        self.center_window()

    def start_move(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def stop_move(self, event):
        self._offset_x = 0
        self._offset_y = 0

    def do_move(self, event):
        x = self.winfo_x() + event.x - self._offset_x
        y = self.winfo_y() + event.y - self._offset_y
        self.geometry(f"+{x}+{y}")

    def minimize_window(self):
        # Временно возвращаем стандартное оформление для корректной работы минимизации
        self.overrideredirect(False)
        self.iconify()
        # После разворачивания снова убираем стандартный заголовок

        self.after(250, lambda: self.bind('<FocusIn>', self.on_deiconify))

    def on_deiconify(self, event):
        self.overrideredirect(True)
        self.unbind("<FocusIn>")

    def quit_app(self):
        self.quit()
        self.destroy()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def mainloop(self, n=0):
        # Центрируем окно перед запуском основного цикла
        self.center_window()
        super().mainloop(n)


class Win(tkinter.Tk):
    """усовершенствованное окно (Tk)"""
    def __init__(self):
        super().__init__()
        self.loops = {}

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
        self.loops.update({target: ms})
        def _loop_wrp(*args):
            _r = target()
            if _r != -1:
                self.after(ms, _loop_wrp, args)
            else:
                self.loops.pop(target)

        _loop_wrp(*_args)

    def mainloop(self, n = 0):
        try:
            super().mainloop(n)
        except Exception as _main_lp_ex:
            print(f'[!!] {self} mainloop failed {_main_lp_ex.__class__} {_main_lp_ex}')



class ListFrames(tkinter.Frame):
    """область для создания виджетов с прокруткой"""
    def __init__(self, **kwargs):
        # scheme:
        # root_frame -> canvas -> scrollable_frame
        super().__init__(**kwargs)
        root_frame = self

        canvas = tkinter.Canvas(root_frame, highlightthickness=0)

        scrollable_frame = tkinter.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

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
        self.for_w = scrollable_frame

    def scroll_to_bottom(self):
        """Прокручивает область просмотра до самого низа"""
        self.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.for_w.event_generate("<Configure>")
        self.canvas.yview_moveto(1.0)  # 1.0 означает 100% прокрутки вниз
        self.canvas.update_idletasks()  # Обновляем отображение


class Popup(tkinter.Frame):
    def __init__(self, master: Win | tkinter.Tk = None, size=None,
                 style=None, title: str = 'Popup', map_on_init=True):
        #if master is None:
        #    raise TypeError(f'Master win is not provided: {app_root_window}')
        if size is None:
            size = [300, 300]
        self.style = style
        self.size = size

        if style is None:
            style = [tkinter.Label()['bg'], tkinter.Label()['fg'], tkinter.Label()['font']]


        self.root_frame = tkinter.Frame(master, width=size[0], height=size[1], highlightthickness=2)
        self.root_frame.pack_propagate(True)


        self.close_btn = tkinter.Button(self.root_frame, text='X', command=self.root_frame.place_forget)
        self.close_btn.pack(anchor='ne')
        self.title_lbl = tkinter.Label(self.root_frame, text=title)
        self.title_lbl.place(x=0, y=0)

        super().__init__(self.root_frame, width=size[0], height=size[1], highlightthickness=2)
        self.pack_propagate(True)

        if style is not None:
            self.configure(bg=style[0], highlightcolor=style[1])
            self.root_frame.configure(bg=style[0], highlightcolor=style[1])
            self.close_btn.configure(bg=style[0], fg=style[1], font=style[2])
            self.title_lbl.configure(bg=style[0], fg=style[1], font=style[2])

        self.root_frame.bind('<Button-1>', self._start_move)
        self.root_frame.bind('<B1-Motion>', self._move)

        self._start_x = 0
        self._start_y = 0

        popups.append(self)

        if map_on_init:
            self.root_frame.place(x=0, y=0)
            self.pack()

    def destroy(self):
        self.root_frame.place_forget()

    def update_idletasks(self):
        super().update_idletasks()
        self.root_frame.update_idletasks()
        self.size = [self.root_frame.winfo_width(), self.root_frame.winfo_height()]
        print(self.size)


    def lift(self):
        self.root_frame.lift()

    def _start_move(self, event=None):
        self.root_frame.lift()
        if hasattr(event, 'x') and hasattr(event, 'y'):
            self._start_x = event.x
            self._start_y = event.y

    def _move(self, event):
        x = self.root_frame.winfo_x() + (event.x - self._start_x)
        y = self.root_frame.winfo_y() + (event.y - self._start_y)
        #self.title_lbl['text'] = f'{self.root_frame.winfo_x()}/{self.root_frame.master.winfo_width() - self.root_frame.winfo_width()} {self.root_frame.winfo_y()}/{self.root_frame.master.winfo_height() - self.root_frame.winfo_height()}'
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

        self.entry = tkinter.Entry(self._root_frame, textvariable=self.var, state=state)
        self.entry.pack(fill='y', expand=True, side='left')
        self.btn = tkinter.Button(self._root_frame, text="▼", command=self.toggle_listbox)
        self.btn.pack(fill='y', expand=True, side='right')
        self.listbox = tkinter.Listbox(bg="white")

        if bg is None:
            bg = tkinter.Label()["background"]  # Берем значение по умолчанию
        if fg is None:
            fg = tkinter.Label()["foreground"]

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

        for value in values:
            self.listbox.insert('end', value)

        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self._root_frame.bind('<Unmap>', lambda e: self.pack_forget())
        self.entry.bind("<KeyRelease>", self.filter_values)
        self.entry.bind("<Down>", lambda e: self.show_listbox())

        if debug:
            d = Win()
            statuses = tkinter.Label(d)
            statuses.pack()

            def upd_status():
                statuses['text'] = f'IsmappedRframe:{self._root_frame.winfo_ismapped()}\nIsmappedListboxSel:{self.listbox.winfo_ismapped()}'

            d.create_loop(upd_status)

    def build(self, mode: Literal['place', 'pack', 'grid'], **kw):
        if mode == 'place':
            self._root_frame.place(**kw)
        elif mode == 'pack':
            self._root_frame.pack(**kw)
        else:
            self._root_frame.grid(**kw)

    def toggle_listbox(self):
        if self.listbox.winfo_ismapped():
            print('hide')
            self.hide_listbox()
        else:
            print('show')
            self.show_listbox()

    def show_listbox(self):
        self.listbox.place(x=self.entry.winfo_rootx() - self.entry.winfo_toplevel().winfo_rootx(),
                           y=self.entry.winfo_rooty() - self.entry.winfo_toplevel().winfo_rooty() + self.entry.winfo_height(),
                           anchor='nw',
                           width=self.entry.winfo_width() + self.btn.winfo_width())
        print(self.entry.winfo_rootx(), self.entry.winfo_rooty())
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
            print(f'binding {_p} to P{_a}')
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