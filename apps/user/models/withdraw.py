from django.contrib.auth import get_user_model
from django.db import models

from apps.core.models import TimeStampedModel

User = get_user_model()


class WithdrawalReason(models.TextChoices):
    GRADUATION = "GRADUATION", "졸업 및 수료"
    TRANSFER = "TRANSFER", "편입 및 전학"
    NO_LONGER_NEEDED = "NO_LONGER_NEEDED", "더 이상 필요하지 않음"
    SERVICE_DISSATISFACTION = "SERVICE_DISSATISFACTION", "서비스 불만족"
    PRIVACY_CONCERN = "PRIVACY_CONCERN", "개인정보 보호 우려"
    OTHER = "OTHER", "기타"


class Withdrawal(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=30, choices=WithdrawalReason.choices)
    reason_detail = models.TextField()
    due_date = models.DateField()

    class Meta:
        db_table = "withdrawals"
