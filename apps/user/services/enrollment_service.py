from __future__ import annotations

from rest_framework import serializers

from apps.courses.models.cohorts_models import Cohort
from apps.user.models import CohortStudent, StudentEnrollmentRequest, User


def enroll_student(*, user: User, cohort: Cohort) -> StudentEnrollmentRequest:
    if CohortStudent.objects.filter(user=user, cohort=cohort).exists():
        raise serializers.ValidationError("이미 수강 중인 기수입니다.")

    if StudentEnrollmentRequest.objects.filter(user=user, cohort=cohort).exists():
        raise serializers.ValidationError("이미 수강 신청한 기수입니다.")

    return StudentEnrollmentRequest.objects.create(user=user, cohort=cohort)
