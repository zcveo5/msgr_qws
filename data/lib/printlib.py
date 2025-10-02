import sys
import time
from data.lib import env

print_lib_root = sys.stdout

def find_h(name):
    try:
        return env.env[f'LogPrintLib{name}']
    except KeyError:
        return sys.stdout


def printin(s, h):
    """утилита для записи строки в stdout / stderr с добавлением перевода строки.

        args:
            s (str): строка для записи
            h (file): файловый объект для записи
        """
    h.write(f'{s}\n')


def print_adv(*s, h=None):
    if h is None:
        h = print_lib_root
    _s = ''
    for i in s:
        _s += str(i) + ' '
    if not _s.startswith('['):
        _s = ' ' + _s
    printin(f'[{time.strftime("%H:%M:%S")}][{h.name}]{_s}', h)