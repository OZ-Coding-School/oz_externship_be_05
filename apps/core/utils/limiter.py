"""
ITS OVER NINE THOUSAND

=========================
Twilio billing statement

96767 sms requests : 9067.5$
67 coffees : 112.51$
surtax : 6.07$

total : 9041.67$

thx for being a sucker we're rich now $$$ 👍
=========================

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from django.core.cache import caches
from rest_framework.exceptions import APIException, ValidationError


class RateLimitSuspendedError(APIException):
    status_code = 503
    default_detail = "현재 사용자가 많아 해당 서비스를 이용 할 수 없습니다. 1분 후 다시 시도해주세요"
    default_code = "rate_limit_suspended"


def _default_cooldown_error() -> Exception:
    return ValidationError("아직 재시도 할 수 없습니다.")


def _default_suspend_error() -> Exception:
    return RateLimitSuspendedError()


@dataclass(frozen=True)
class IPWorkPolicy:
    work: str
    cache_alias: str = "default"
    ip_cooldown_seconds: int = 30
    global_limit_per_minute: int = 1000
    global_suspend_seconds: int = 60
    cooldown_error_factory: Callable[[], Exception] = _default_cooldown_error
    suspend_error_factory: Callable[[], Exception] = _default_suspend_error


class IPBasedRateLimiter:
    def __init__(self, policy: IPWorkPolicy):
        self.policy = policy

    def _cache(self) -> Any:
        return caches[self.policy.cache_alias]

    def _global_count_key(self) -> str:
        return f"global:{self.policy.work}:count:minute"

    def _global_suspend_key(self) -> str:
        return f"global:{self.policy.work}:suspend"

    def _ip_cooldown_key(self, ip_address: str) -> str:
        return f"ip:{ip_address}:{self.policy.work}:cooldown"

    def enforce(self, request_ip: Optional[str]) -> None:
        cache = self._cache()
        suspend_key = self._global_suspend_key()
        if cache.get(suspend_key):
            raise self.policy.suspend_error_factory()

        count_key = self._global_count_key()
        if cache.add(count_key, 1, 60):
            count = 1
        else:
            try:
                count = cache.incr(count_key)
            except Exception:
                current = cache.get(count_key) or 0
                count = int(current) + 1
                cache.set(count_key, count, 60)

        if count > self.policy.global_limit_per_minute:
            cache.set(suspend_key, "1", self.policy.global_suspend_seconds)
            raise self.policy.suspend_error_factory()

        if request_ip:
            key = self._ip_cooldown_key(request_ip)
            if not cache.add(key, "1", self.policy.ip_cooldown_seconds):
                raise self.policy.cooldown_error_factory()
