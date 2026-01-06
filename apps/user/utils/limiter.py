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

from django.conf import settings
from rest_framework.exceptions import APIException, ValidationError

from apps.core.utils.limiter import IPBasedRateLimiter, IPWorkPolicy


class SMSSuspendedError(APIException):
    status_code = 503
    default_detail = "SMS 인증서비스에 사용자가 몰려 현재 이용 할 수 없습니다. 나중에 다시 시도해주세요."
    default_code = "sms_service_suspended"


def build_sms_rate_limiter() -> IPBasedRateLimiter:
    work_name = getattr(settings, "SMS_RATE_WORK_NAME", "smsverification")
    policy = IPWorkPolicy(
        work=work_name,
        cache_alias="default",
        ip_cooldown_seconds=int(getattr(settings, "SMS_RATE_IP_COOLDOWN_SECONDS", 30)),
        global_limit_per_minute=int(getattr(settings, "SMS_RATE_GLOBAL_LIMIT_PER_MINUTE", 1000)),
        global_suspend_seconds=int(getattr(settings, "SMS_RATE_GLOBAL_SUSPEND_SECONDS", 60)),
        cooldown_error_factory=lambda: ValidationError("SMS 인증 요청은 30초마다 가능합니다."),
        suspend_error_factory=SMSSuspendedError,
    )
    return IPBasedRateLimiter(policy)
