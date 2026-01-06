from __future__ import annotations

import base64
import secrets
from typing import Any, Optional

from django.conf import settings
from django.core.cache import caches

CODE_LENGTH = settings.VERIFICATION_CODE_LENGTH
TOKEN_BYTES = settings.VERIFICATION_TOKEN_BYTES
CODE_CHARS = settings.VERIFICATION_CODE_CHARS
DEFAULT_TTL_SECONDS = settings.VERIFICATION_DEFAULT_TTL_SECONDS
TOKEN_GENERATE_MAX_ATTEMPTS = settings.VERIFICATION_TOKEN_GENERATE_MAX_ATTEMPTS


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

    def _code_key(self, identifier: str) -> str:
        return f"{self.namespace}:code:{identifier}"

    def _token_lookup_key(self, token: str) -> str:
        return f"{self.namespace}:token:{token}"

    def _cache(self) -> Any:
        return caches[self.redis_alias]

    def generate_code(self, identifier: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
        normalized = _normalize_identifier(identifier)
        code = "".join(secrets.choice(CODE_CHARS) for _ in range(self.code_length))
        cache = self._cache()
        cache.set(self._code_key(normalized), code, ttl_seconds)
        return code

    def generate_token(self, identifier: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
        normalized = _normalize_identifier(identifier)
        cache = self._cache()

        for _ in range(TOKEN_GENERATE_MAX_ATTEMPTS):
            raw = secrets.token_bytes(self.token_bytes)
            token = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
            if cache.add(self._token_lookup_key(token), normalized, ttl_seconds):
                return token

        raise RuntimeError("failed to generate a unique token. try later!")

    def verify(self, identifier: str, submitted_code: str, consume: bool = True, is_token: bool = False) -> bool:
        normalized = _normalize_identifier(identifier)

        if is_token:
            identifier_from_token = self.verify_token(submitted_code, consume=consume)
            return identifier_from_token == normalized

        cache = self._cache()
        key = self._code_key(normalized)
        stored = cache.get(key)
        if stored is None:
            return False

        stored_str = stored.decode() if isinstance(stored, (bytes, bytearray)) else stored
        matched: bool = stored_str == submitted_code

        if matched and consume:
            cache.delete(key)

        return matched

    def verify_token(self, token: str, consume: bool = True) -> Optional[str]:
        cache = self._cache()
        lookup_key = self._token_lookup_key(token)
        value = cache.get(lookup_key)
        if value is None:
            return None
        identifier = value.decode() if isinstance(value, (bytes, bytearray)) else value
        if consume:
            cache.delete(lookup_key)
        return identifier

    def get_remaining_ttl(self, identifier: str, is_token: bool = False) -> Optional[int]:
        cache = self._cache()
        key = self._token_lookup_key(identifier) if is_token else self._code_key(_normalize_identifier(identifier))
        ttl_method = getattr(cache, "ttl", None)
        if ttl_method is None:
            return None
        ttl = ttl_method(key)
        if ttl is None or ttl < 0:
            return None
        return int(ttl)

    def delete(self, identifier: str, is_token: bool = False) -> None:
        cache = self._cache()
        if is_token:
            cache.delete(self._token_lookup_key(identifier))
        else:
            cache.delete(self._code_key(_normalize_identifier(identifier)))

    def get_identifier_by_token(self, token: str) -> Optional[str]:
        return self.verify_token(token, consume=False)
