from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models.cohorts_models import Cohort
from apps.user.models.user import User


class EnrollmentStatus(models.TextChoices):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class StudentEnrollmentRequest(TimeStampedModel):
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=EnrollmentStatus.choices, default=EnrollmentStatus.PENDING)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "student_enrollment_requests"
