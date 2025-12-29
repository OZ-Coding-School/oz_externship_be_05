from __future__ import annotations

from datetime import date

from django.db.models import QuerySet
from django.utils import timezone

from apps.courses.models.cohorts_models import Cohort, CohortStatusChoices
from apps.user.models import CohortStudent, User


def get_available_cohorts_queryset(*, now_date: date | None = None) -> QuerySet[Cohort]:
    base_date = now_date or timezone.localdate()
    return Cohort.objects.filter(status=CohortStatusChoices.PENDING, start_date__gte=base_date)


def get_user_enrolled_cohort_students(*, user: User) -> QuerySet[CohortStudent]:
    return CohortStudent.objects.filter(user=user).select_related("cohort", "cohort__course")
