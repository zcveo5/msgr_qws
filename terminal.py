import runpy
import sys
import threading
import time
import tkinter


def terminal_thread():
    time.sleep(0.5)
    def execute(event):
        exec(event.widget.get())
    ter = tkinter.Tk()
    ter.title('terminal')
    exec_line = tkinter.Entry()
    exec_line.pack()
    exec_line.bind('<Return>', execute)
    ter.mainloop()

threading.Thread(target=terminal_thread, daemon=True).start()

file_path = 'msgr.py'
result = runpy.run_path(
    file_path,
    run_name='__main__',
    init_globals={'__name__': '__main__'}
)
sys.modules['msgr'] = type(sys)('msgr')
sys.modules['msgr'].__dict__.update(result)
