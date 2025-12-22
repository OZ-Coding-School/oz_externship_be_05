from typing import Any

from rest_framework import serializers

from apps.user.models import User
from apps.user.models.user import RoleChoices
from apps.user.serializers.admin.common import (
    CohortMiniSerializer,
    CourseMiniSerializer,
    StatusMixin,
)


# 계정 목록 조회 시리얼라이저
class AdminAccountListSerializer(StatusMixin, serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ("id", "email", "nickname", "name", "birthday", "status", "role", "created_at")