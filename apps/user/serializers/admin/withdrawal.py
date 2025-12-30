from typing import Any

from rest_framework import serializers

from apps.user.models.withdraw import Withdrawal
from apps.user.serializers.admin.common import (
    CohortMiniSerializer,
    CourseMiniSerializer,
    UserWithdrawalDetailMiniSerializer,
    UserWithdrawalMiniSerializer,
)


class AdminAccountWithdrawalListSerializer(serializers.ModelSerializer[Withdrawal]):
    user = UserWithdrawalMiniSerializer(read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    withdrawn_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Withdrawal
        fields = ("id", "user", "reason", "reason_display", "withdrawn_at")


class CohortStudentAssignedSerializer(serializers.Serializer[dict[str, Any]]):
    cohort: CohortMiniSerializer = CohortMiniSerializer(read_only=True)
    course: CourseMiniSerializer = CourseMiniSerializer(source="cohort.course", read_only=True)


class AdminAccountWithdrawalRetrieveSerializer(serializers.ModelSerializer[Withdrawal]):
    user: UserWithdrawalDetailMiniSerializer = UserWithdrawalDetailMiniSerializer(read_only=True)
    reason_display: serializers.CharField = serializers.CharField(source="get_reason_display", read_only=True)
    withdrawn_at: serializers.DateTimeField = serializers.DateTimeField(source="created_at", read_only=True)

    assigned_courses: CohortStudentAssignedSerializer = CohortStudentAssignedSerializer(
        source="user.cohortstudent_set",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Withdrawal
        fields = (
            "id",
            "user",
            "assigned_courses",
            "reason",
            "reason_display",
            "reason_detail",
            "due_date",
            "withdrawn_at",
        )
