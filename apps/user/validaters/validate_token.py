import base64
import binascii
import re

CODE_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def is_valid_token_format(token: str, token_bytes: int) -> bool:
    if not isinstance(token, str):
        return False
    if not CODE_PATTERN.fullmatch(token):
        return False

    padding = "=" * (-len(token) % 4)  # 추운 겨울 따듯한 패딩

    try:
        raw = base64.urlsafe_b64decode(token + padding)
    except (binascii.Error, ValueError):
        return False
    return len(raw) == token_bytes
