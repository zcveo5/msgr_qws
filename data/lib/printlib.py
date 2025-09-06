import sys
import time

main_log = sys.stdout

def printin(s, h):
    """утилита для записи строки в stdout / stderr с добавлением перевода строки.

        args:
            s (str): строка для записи
            h (file): файловый объект для записи
        """
    h.write(f'{s}\n')


def print_adv(*s, h=None):
    if h is None:
        h = main_log
    _s = ''
    for i in s:
        _s += str(i) + ' '
    printin(f'[{time.strftime("%H:%M:%S")}][{h.name}]{_s}', h)