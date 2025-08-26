import tkinter
from tkinter import TclError


class Win(tkinter.Tk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
            target()
            self.after(ms, _loop_wrp, args)
        _loop_wrp(*_args)

    def mainloop(self, n = 0):
        try:
            super().mainloop(n)
        except Exception as _main_lp_ex:
            print(f'[!!] {self} mainloop failed {_main_lp_ex.__class__} {_main_lp_ex}')


class ListFrames1:
    def __init__(self, master):
        self.outer_frame = tkinter.Frame(master, highlightthickness=2)

        self.canvas = tkinter.Canvas(
            self.outer_frame,
            highlightthickness=0
        )

        self.v_scroll = tkinter.Scrollbar(
            self.outer_frame,
            orient='vertical',
            command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.v_scroll.set)

        self.h_scroll = tkinter.Scrollbar(
            self.outer_frame,
            orient='horizontal',
            command=self.canvas.xview
        )
        self.canvas.configure(xscrollcommand=self.h_scroll.set)

        #self.canvas.pack_propagate(True)
        self.canvas.pack(anchor='nw', fill='both', expand=True)

        self.inner_frame = tkinter.Frame(self.canvas)
        #self.inner_frame.pack_propagate(True)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.inner_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

        self.canvas.configure(yscrollincrement=1, xscrollincrement=1)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Shift-MouseWheel>", self._on_shift_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Shift-MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * event.delta, "units")

    def _on_shift_mousewheel(self, event):
        self.canvas.xview_scroll(-1 * event.delta, "units")


    def __getattribute__(self, item):
        print(f'[*][LFrames] get attr {item}')
        return super().__getattribute__(item)

    def __getitem__(self, item):
        print(f'[*][LFrames] get item {item}')
        return super().__getattribute__(item)


class ListFrames(tkinter.Frame):
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
            # Изменяем ширину scrollable_frame под текущую ширину canvas
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
