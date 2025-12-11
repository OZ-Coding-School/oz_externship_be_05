from __future__ import annotations

import base64
import secrets
from typing import Any, Optional

from django.conf import settings
from django.core.cache import caches

CODE_LENGTH = settings.VERIFYCATION_CODE_LENGTH
TOKEN_BYTES = settings.VERIFYCATION_TOKEN_BYTES
CODE_CHARS = settings.VERIFYCATION_CODE_CHARS
DEFAULT_TTL_SECONDS = settings.VERIFICATION_DEFAULT_TTL_SECONDS
TOKEN_GENERATE_MAX_ATTEMPTS = settings.VERIFYCATION_TOKEN_GENERATE_MAX_ATTEMPTS


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

    def _token_lookup_key(self, token: str) -> str:  # token을 키로 가지고 identifier를 value로 가져 역참조 가능
        return f"{self.namespace}:token_lookup:{token}"

    def _cache(self) -> Any:
        return caches[self.redis_alias]

    # 생성
    def generate_code(self, identifier: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
        normalized = _normalize_identifier(identifier)
        code = "".join(secrets.choice(CODE_CHARS) for _ in range(self.code_length))
        cache = self._cache()
        cache.set(self._code_key(normalized), code, ttl_seconds)
        return code

    def generate_token(self, identifier: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
        normalized = _normalize_identifier(identifier)
        cache = self._cache()

        # 기존 토큰 역참조 정리
        previous = cache.get(self._token_key(normalized))
        if previous:
            previous_token = previous.decode() if isinstance(previous, (bytes, bytearray)) else previous
            cache.delete(self._token_lookup_key(previous_token))

        max_attempts = TOKEN_GENERATE_MAX_ATTEMPTS
        for _ in range(max_attempts):
            raw = secrets.token_bytes(self.token_bytes)
            token = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
            added = cache.add(self._token_lookup_key(token), normalized, ttl_seconds)
            if not added:
                continue
            if cache.set(self._token_key(normalized), token, ttl_seconds):
                return token
            cache.delete(self._token_lookup_key(token))
        raise RuntimeError("failed to generate a unique token. try later!")

    # 검증
    def verify(self, identifier: str, submitted_code: str, consume: bool = True, is_token: bool = False) -> bool:
        normalized = _normalize_identifier(identifier)
        cache = self._cache()
        key = self._token_key(normalized) if is_token else self._code_key(normalized)
        stored = cache.get(key)
        if stored is None:
            return False

        stored_str = stored.decode() if isinstance(stored, (bytes, bytearray)) else stored
        matched: bool = stored_str == submitted_code

        if matched and consume:
            if is_token:
                cache.delete_many([key, self._token_lookup_key(submitted_code)])
            else:
                cache.delete(key)

        return matched

    # 조회/ 유효기간 지났으먼 삭제
    def get_remaining_ttl(self, identifier: str, is_token: bool = False) -> Optional[int]:
        cache = self._cache()
        key = (
            self._token_key(_normalize_identifier(identifier))
            if is_token
            else self._code_key(_normalize_identifier(identifier))
        )
        ttl_method = getattr(cache, "ttl", None)
        if ttl_method is None:
            return None
        ttl = ttl_method(key)
        if ttl is None or ttl < 0:
            return None
        return int(ttl)

    def delete(self, identifier: str, is_token: bool = False) -> None:
        normalized = _normalize_identifier(identifier)
        cache = self._cache()
        if is_token:
            token_key = self._token_key(normalized)
            token = cache.get(token_key)
            token_value = token.decode() if isinstance(token, (bytes, bytearray)) else token
            keys = [token_key]
            if token_value:
                keys.append(self._token_lookup_key(token_value))
            cache.delete_many(keys)
        else:
            cache.delete(self._code_key(normalized))

    def get_identifier_by_token(self, token: str) -> str:
        cache = self._cache()
        value = cache.get(self._token_lookup_key(token))
        if value is None:
            return None
        return value.decode() if isinstance(value, (bytes, bytearray)) else value
