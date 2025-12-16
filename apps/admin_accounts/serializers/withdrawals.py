from rest_framework import serializers
from apps.user.models.withdraw import Withdrawal
from .common import (
    UserWithdrawalMiniSerializer,
    UserWithdrawalDetailMiniSerializer,
    CourseMiniSerializer,
    CohortMiniSerializer,
)

class AdminAccountWithdrawalListSerializer(serializers.ModelSerializer):
    user = UserWithdrawalMiniSerializer(read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    withdrawn_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Withdrawal
        fields = ("id","user","reason","reason_display","withdrawn_at")

class AdminAccountWithdrawalRetrieveSerializer(serializers.ModelSerializer):
    user = UserWithdrawalDetailMiniSerializer(read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    withdrawn_at = serializers.DateTimeField(source="created_at", read_only=True)
    assigned_courses = serializers.SerializerMethodField()

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

    def get_assigned_courses(self, obj: Withdrawal):
        result = []
        for cs in obj.user.cohort_students.all():
            cohort = cs.cohort
            if not cohort:
                continue
            result.append({
                "course": CourseMiniSerializer(cohort.course).data,
                "cohort": CohortMiniSerializer(cohort).data,
            })
        return result