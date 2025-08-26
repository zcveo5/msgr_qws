import json
import data.lib.jsoncrypt as jsoncrypt


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
            print(f'[*] backup {self._fp}')
            json.dump(self._dct, open(self._fp, 'w'))
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
            print(f'[*] backup {self._fp}')
            jsoncrypt.dump(self._dct, open(self._fp, 'w+'))
            self._dct = jsoncrypt.load(open(self._fp, 'r'))