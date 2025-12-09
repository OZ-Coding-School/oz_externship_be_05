from __future__ import annotations

import random
import string
from typing import Optional

from django_redis import get_redis_connection  # type: ignore[import-untyped]

DEFAULT_TTL_SECONDS = 600
CODE_LENGTH = 6
REDIS_PREFIX = "verification:code:"
# prefix를 고정할지 말지 고민 예를들면 email은 prefix를 email:identifier 로 할지 같은거
# 근데 어차피 이메일하고 전화번호는 구분이 필요하니깐 그냥 고정하는게 나을수도


def _build_key(identifier: str) -> str:
    return f"{REDIS_PREFIX}{identifier}"


def generate_code(identifier: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
    """코드를 생성 및 캐시에 저장합니다
    Args:
        identifier (str): 코드를 식별할 고유 문자열 (예: 이메일, 전화번호)
        ttl_seconds (int, optional): 코드의 유효 기간(초). 기본값 : DEFAULT_TTL_SECONDS(600).
    Returns:
        str: 생성된 코드
    """
    code = "".join(random.choices(string.digits, k=CODE_LENGTH))  # CODE_LENGTH 길이의 코드 생성
    conn = get_redis_connection("default")
    conn.set(_build_key(identifier), code, ex=ttl_seconds)
    return code


def verify_code(identifier: str, submitted_code: str, consume: bool = True) -> bool:
    """코드를 생성 및 캐시에 저장합니다
    Args:
        identifier (str): 코드를 식별할 고유 문자열 (예: 이메일, 전화번호)
        submitted_code (str): 사용자가 제출한 코드
        consume (bool, optional): 검증 후 코드를 삭제할지 여부. 기본값 = True.
    Returns:
        str: 생성된 코드
    """
    conn = get_redis_connection("default")
    stored = conn.get(_build_key(identifier))
    if stored is None:
        return False

    stored_str = stored.decode()
    matched: bool = stored_str == submitted_code

    if matched and consume:
        conn.delete(_build_key(identifier))

    return matched


def get_remaining_ttl(identifier: str) -> Optional[int]:
    """남은 시간을 조회합니다.
    Args:
        identifier (str): 코드를 식별할 고유 문자열 (예: 이메일, 전화번호)
    Returns:
        Optional[int]: 남은 시간(초). 없으면 None 반환.
    """
    conn = get_redis_connection("default")
    ttl = conn.ttl(_build_key(identifier))
    if ttl is None or ttl < 0:
        return None
    return int(ttl)


def delete_code(identifier: str) -> None:
    """코드를 삭제합니다.
    Args:
        identifier (str): 코드를 식별할 고유 문자열 (예: 이메일, 전화번호)
    """
    conn = get_redis_connection("default")
    conn.delete(_build_key(identifier))
