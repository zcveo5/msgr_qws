import json


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
        print(f'[*] backup {self._fp}')
        json.dump(self._dct, open(self._fp, 'w'))
        self._dct = json.load(open(self._fp, 'r'))

    def keys(self):
        return self._dct.keys()

    def values(self):
        return self._dct.values()


class Theme:
    def __init__(self, fp):
        self._dct = json.load(open(f'./data/theme/{fp}.json', 'r'))
        self.bg = self._dct['bg']
        self.fg = self._dct['fg']
        self.font = self._dct['font']


class Locale(UserData):
    def __init__(self, fp):
        super().__init__(open(f'./data/locale/{fp}.json', 'r'))

    def get(self, item, default):
        try:
            return super().__getitem__(item)
        except KeyError:
            return default

    def backup(self):
        ...
