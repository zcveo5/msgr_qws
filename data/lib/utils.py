import json
import threading
import time

import data.lib.jsoncrypt as jsoncrypt
import random
from data.lib.printlib import print_adv


def randgen(c=25):
    symb = "A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z, B, C, D, F, G, H, J, K, L, M, N, P, Q, R, S, T, V, W, X, Y, Z".split(', ')
    random.shuffle(symb)
    link = ''
    ints = random.randint(1000000, 9999999)
    for i in range(0, c):
        if i % 3 == 0:
            link += str(ints)[random.randint(0, 6)]
        else:
            _e = symb[random.randint(0, len(symb) - 1)]
            if random.randint(0, 1) == 1:
                link += _e.lower()
            else:
                link += _e
    return link


class UserData:
    def __init__(self, fp: open):
        self._fp = fp.name
        self._dct = json.load(fp)

    def __getitem__(self, item):
        return self._dct[item]

    def __setitem__(self, key, value):
        self._dct[key] = value
        self.backup()

    def __iter__(self):
        return self._dct.__iter__()

    def backup(self):
        if self._dct != json.load(open(self._fp, 'r')):
            print_adv(f'[*] backup {self._fp}')
            json.dump(self._dct, open(self._fp, 'w'), indent=4)
            self._dct = json.load(open(self._fp, 'r'))

    def keys(self):
        return self._dct.keys()

    def values(self):
        return self._dct.values()

    def __eq__(self, other):
        return self._dct == other


class Theme:
    def __init__(self, fp):
        self._dct = json.load(open(f'./data/theme/{fp}.json', 'r'))
        self.bg = self._dct['bg']
        self.fg = self._dct['fg']
        self.font = self._dct['font']


class Locale(UserData):
    def __init__(self, fp):
        super().__init__(open(f'./data/locale/{fp}.json', 'r', encoding='utf-8'))

    def get(self, item, default):
        to_return = ''
        try:
            to_return = super().__getitem__(item)
        except KeyError:
            to_return = default
        to_return = _LocaleElement(to_return)
        to_return.set_locale_key(item)
        return to_return

    def backup(self):
        ...


class _LocaleElement(str):
    def set_locale_key(self, key):
        self.locale_key = key


class EncryptedUserData(UserData):
    def __init__(self, fp: open):
        self._fp = fp.name
        self._dct = jsoncrypt.load(fp)

    def backup(self):
        if self._dct != jsoncrypt.load(open(self._fp, 'r')):
            print_adv(f'[*] backup {self._fp}')
            jsoncrypt.dump(self._dct, open(self._fp, 'w+'))
            self._dct = jsoncrypt.load(open(self._fp, 'r'))


def create_loop(target, s, *args):
    def _loop_wrp(*_a):
        while True:
            target(*_a)
            time.sleep(s)
    _th = threading.Thread(target=_loop_wrp, daemon=True, args=args)


def after(target, s, *args):
    def _after_wrp(*_a):
        time.sleep(s)
        target(*_a)
    _th = threading.Thread(target=_after_wrp, daemon=True, args=args)