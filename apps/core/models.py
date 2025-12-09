from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시 자동 기록
    updated_at = models.DateTimeField(auto_now=True)  # 저장될 때 자동 갱신

    class Meta:
        abstract = True  # 테이블을 생성하지 않음
