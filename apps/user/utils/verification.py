from __future__ import annotations

import base64
import secrets
from typing import Any, Optional

from django_redis import get_redis_connection

# [ verification settings ]
DEFAULT_TTL_SECONDS = 300
TOKEN_GENERATE_MAX_ATTEMPTS = 5
CODE_LENGTH = 6
TOKEN_BYTES = 32
CODE_CHARS = "0123456789"
# config/settings/base에 분리 필요시 pr 반려해주시길 바랍니다.


def _normalize_identifier(identifier: str) -> str:
    return identifier.strip().lower()


class VerificationService:
    def __init__(
        self,
        redis_alias: str = "default",
        namespace: str = "verification",
        code_length: int = CODE_LENGTH,
        token_bytes: int = TOKEN_BYTES,
    ) -> None:
        self.redis_alias = redis_alias
        self.namespace = namespace
        self.code_length = code_length
        self.token_bytes = token_bytes

    # 키 빌더
    def _code_key(self, identifier: str) -> str:
        return f"{self.namespace}:code:{identifier}"

    def _token_key(self, identifier: str) -> str:
        return f"{self.namespace}:token:{identifier}"

    def _token_lookup_key(self, token: str) -> str:  # 토큰으로 identifier 찾기 (identifer를 키로 가짐)
        return f"{self.namespace}:token_lookup:{token}"

    def _conn(self) -> Any:
        return get_redis_connection(self.redis_alias)

    # 생성
    def generate_code(self, identifier: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
        normalized = _normalize_identifier(identifier)
        digits = CODE_CHARS
        code = "".join(secrets.choice(digits) for _ in range(self.code_length))
        conn = self._conn()
        conn.set(self._code_key(normalized), code, ex=ttl_seconds)
        return code

    def generate_token(self, identifier: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
        normalized = _normalize_identifier(identifier)
        conn = self._conn()

        # 기존 토큰 역참조 정리
        previous = conn.get(self._token_key(normalized))
        if previous:
            conn.delete(self._token_lookup_key(previous.decode()))

        max_attempts = TOKEN_GENERATE_MAX_ATTEMPTS
        for _ in range(max_attempts):
            raw = secrets.token_bytes(self.token_bytes)
            token = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
            if conn.setnx(self._token_lookup_key(token), normalized):
                pipe = conn.pipeline()
                pipe.expire(self._token_lookup_key(token), ttl_seconds)
                pipe.set(self._token_key(normalized), token, ex=ttl_seconds)
                pipe.execute()
                return token
        raise RuntimeError("failed to generate a unique token. try later!")

    # 검증
    def verify(self, identifier: str, submitted_code: str, consume: bool = True, is_token: bool = False) -> bool:
        normalized = _normalize_identifier(identifier)
        conn = self._conn()
        key = self._token_key(normalized) if is_token else self._code_key(normalized)
        stored = conn.get(key)
        if stored is None:
            return False

        stored_str = stored.decode()
        matched: bool = stored_str == submitted_code

        if matched and consume:
            pipe = conn.pipeline()
            pipe.delete(key)
            if is_token:
                pipe.delete(self._token_lookup_key(submitted_code))
            pipe.execute()

        return matched

    # 조회/삭제
    def get_remaining_ttl(self, identifier: str, is_token: bool = False) -> Optional[int]:
        conn = self._conn()
        key = (
            self._token_key(_normalize_identifier(identifier))
            if is_token
            else self._code_key(_normalize_identifier(identifier))
        )
        ttl = conn.ttl(key)
        if ttl is None or ttl < 0:
            return None
        return int(ttl)

    def delete(self, identifier: str, is_token: bool = False) -> None:
        conn = self._conn()
        normalized = _normalize_identifier(identifier)
        key = self._token_key(normalized) if is_token else self._code_key(normalized)
        pipe = conn.pipeline()
        pipe.delete(key)
        if is_token:
            pipe.delete(self._token_lookup_key(normalized))
        pipe.execute()

    def get_identifier_by_token(self, token: str) -> Optional[str]:
        conn = self._conn()
        value = conn.get(self._token_lookup_key(token))
        return value.decode() if value else None


_default_service = VerificationService()


def generate_code(identifier: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
    return _default_service.generate_code(identifier, ttl_seconds)


def generate_token(identifier: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
    return _default_service.generate_token(identifier, ttl_seconds)


def verify(identifier: str, submitted_code: str, consume: bool = True, is_token: bool = False) -> bool:
    return _default_service.verify(identifier, submitted_code, consume, is_token)


def get_remaining_ttl(identifier: str, is_token: bool = False) -> Optional[int]:
    return _default_service.get_remaining_ttl(identifier, is_token)


def delete(identifier: str, is_token: bool = False) -> None:
    return _default_service.delete(identifier, is_token)


def get_identifier_by_token(token: str) -> Optional[str]:
    return _default_service.get_identifier_by_token(token)
