import random

SYMBOLS = list(
    "\nqwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
    "1234567890~!@#$%^&*()_+-=?><,./|\\\"'[]{}:; "
    "йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ"
)


def shift_string(s: str, step: int) -> str:
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


def generate_salt() -> str:
    shuffled = SYMBOLS.copy()
    random.shuffle(shuffled)
    substitution_map = {SYMBOLS[i]: shuffled[i] for i in range(len(SYMBOLS))}
    step_value = random.randint(0, 100)
    substitution_map['stp'] = step_value
    map_string = str(substitution_map)
    salt = _encrypt_key(map_string)
    return salt


def _encrypt_key(key_string: str) -> str:
    step = random.randint(10, 99)
    encrypted = shift_string(key_string, step)
    return f"{step:02d}{encrypted}"


def _decrypt_key(encrypted_key: str) -> dict:
    step = int(encrypted_key[:2])
    rest = encrypted_key[2:]
    decrypted = shift_string(rest, -step)
    return eval(decrypted)


def encrypt(data: str, salt: str) -> str:
    salt_dict = _decrypt_key(salt)
    step_value = salt_dict.pop('stp')
    encrypted_chars = [salt_dict.get(char, '?') for char in data]
    result = ''.join(encrypted_chars)
    return shift_string(result, step_value)


def decrypt(data: str, salt: str) -> str:
    salt_dict = _decrypt_key(salt)
    step_value = salt_dict.pop('stp')
    unshifted = shift_string(data, -step_value)
    reverse_map = {v: k for k, v in salt_dict.items()}
    decrypted_chars = [reverse_map.get(char, '?') for char in unshifted]
    return ''.join(decrypted_chars)
