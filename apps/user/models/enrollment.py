from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models.cohorts_models import Cohort
from apps.user.models.user import User


class EnrollmentStatus(models.TextChoices):
    """
    등록 요청 상태를 수정했는데 배포환경 더미데이터에 영향이 갈지 걱정이됨. 내일 물어볼 것
    """

    #! PENDING = "PENDING"
    #! IN_PROGRESS = "IN_PROGRESS"
    #! COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELED = "CANCELED"


class StudentEnrollmentRequest(TimeStampedModel):
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=EnrollmentStatus.choices, default=EnrollmentStatus.PENDING)
    accepted_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "student_enrollment_requests"
