import ast
import random
import sys

"""система шифрования"""


SYMBOLS = ['\n', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'z', 'x', 'c', 'v', 'b', 'n', 'm', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'Z', 'X', 'C', 'V', 'N', 'M', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '-', '=', '?', '>', '<', '/', '|', str(r'\\')[0], '[', ']', '{', '}', ':', ';', ' ', '"', "'", ',', '.', 'й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х', 'ъ', 'ф', 'ы', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'ж', 'э', 'я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю', 'Й', 'Ц', 'У', 'К', 'Е', 'Н', 'Г', 'Ш', 'Щ', 'З', 'Х', 'Ъ', 'Ф', 'Ы', 'В', 'А', 'П', 'Р', 'О', 'Л', 'Д', 'Ж', 'Э', 'Я', 'Ч', 'С', 'М', 'И', 'Т', 'Ь', 'Б', 'Ю']

def shift_string(s: str, step: int) -> str:
    """шифр цезаря"""
    total = len(SYMBOLS)
    result = []

    for char in s:
        if char in SYMBOLS:
            idx = SYMBOLS.index(char)
            new_idx = (idx + step) % total
            result.append(SYMBOLS[new_idx])
        else:
            result.append(char)
    return ''.join(result)


def generate_salt(force_step=-1, __level=0, log=False) -> str:
    """создает ключ"""
    if __level > 0 and log:
        print(f'LEVEL {__level}')
    shuffled = SYMBOLS.copy()
    random.shuffle(shuffled)
    substitution_map = {SYMBOLS[i]: shuffled[i] for i in range(len(SYMBOLS))}
    step_value = random.randint(0, 100)
    if force_step != -1:
        step_value = force_step
    substitution_map['stp'] = step_value
    map_string = str(substitution_map).replace(', ', ',')
    salt = _encrypt_key(map_string, force_step=force_step)
    correct_salt = False
    regenerate_c = 0
    while not correct_salt:
        regenerate_c += 1
        try:
            _s = _decrypt_key(salt)
            for i in SYMBOLS:
                if i not in _s.keys() or i not in _s.values():
                    raise Exception
            correct_salt = True
        except Exception as _salt_gen_ex:
            if log:
                print(f'Invalid salt generated ({_salt_gen_ex.__class__.__name__} at decode), regenerating salt {'' if __level == 0 else str(__level)}', file=sys.stderr)
            salt = generate_salt(force_step, __level+1)
            correct_salt = False
    if regenerate_c > 1 and log:
        print(f'Exited with regen_c: {regenerate_c}')
    return salt


def _encrypt_key(key_string: str, force_step=-1) -> str:
    """защищает ключ"""
    if not isinstance(key_string, str):
        key_string = str(key_string)
    step = random.randint(1, 99)
    if force_step != -1:
        step = force_step
    encrypted = shift_string(key_string, step).replace(', ', ',')
    return f"{step:02d}{encrypted}"


def _decrypt_key(encrypted_key: str) -> dict:
    """расшифровывает ключ"""
    if not isinstance(encrypted_key, str):
        encrypted_key = str(encrypted_key)
    step = int(encrypted_key[:2])
    rest = encrypted_key[2:]
    decrypted = shift_string(rest, -step)
    decrypted = ast.literal_eval(decrypted)
    return decrypted


def encrypt(data: str, salt: str) -> str:
    """шифрует данные"""
    salt_dict = _decrypt_key(salt)
    step_value = salt_dict.pop('stp')
    encrypted_chars = [salt_dict.get(char, '?') for char in data]
    result = ''.join(encrypted_chars)
    _r = shift_string(result, step_value)
    #_r = base64.b64encode(_r.encode('utf-8'))
    #_r = _r.decode('utf-8')
    return _r


def decrypt(data: str, salt: str) -> str:
    """расшифровывает данные"""
    salt_dict = _decrypt_key(salt)
    step_value = salt_dict.pop('stp')
    unshifted = shift_string(data, -step_value)
    reverse_map = {v: k for k, v in salt_dict.items()}
    decrypted_chars = [reverse_map.get(char, '?') for char in unshifted]
    _r = ''.join(decrypted_chars)
    #_r = base64.b64decode(_r.encode('utf-8'))
    #_r = _r.decode('utf-8')
    return _r
