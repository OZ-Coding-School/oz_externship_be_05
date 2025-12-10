from django.db import models

from apps.core.models import TimeStampedModel


class DeploymentStatus(models.TextChoices):
    ACTIVATED = "activated", "활성화"
    DEACTIVATED = "deactivated", "비활성화"


class ExamDeployment(TimeStampedModel):
    """
    시험 배포 정보
    ERD: exam_deployments
    """

    # ERD: cohort_id bigint [not null]
    cohort = models.ForeignKey(
        "courses.Cohort",
        on_delete=models.PROTECT,
        related_name="exam_deployments",
    )

    # ERD: exam_id bigint [not null]
    exam = models.ForeignKey(
        "exams.Exam",
        on_delete=models.PROTECT,
        related_name="deployments",
    )

    # ERD: duration_time tinyint(2) [not null, default: 60]
    duration_time = models.PositiveSmallIntegerField(
        default=60,
        help_text="시험 진행 시간 (분 단위)",
    )

    # ERD: access_code varchar(64) [not null]
    access_code = models.CharField(
        max_length=64,
        unique=True,
        help_text="Base62 인코딩된 참가 코드",
    )

    # ERD: open_at datetime [not null]
    open_at = models.DateTimeField()

    # ERD: close_at datetime [not null]
    close_at = models.DateTimeField()

    # ERD: questions_snapshot_json json [not null]
    questions_snapshot = models.JSONField(
        db_column="questions_snapshot_json",
        help_text="배포 시점의 시험 문항 스냅샷(JSON)",
    )

    # ERD: status enum [default: 'Activated']
    status = models.CharField(
        max_length=32,
        choices=DeploymentStatus.choices,
        default=DeploymentStatus.ACTIVATED,
    )

    class Meta:
        db_table = "exam_deployments"
        verbose_name = "Exam Deployment"
        verbose_name_plural = "Exam Deployments"

    def __str__(self) -> str:
        return f"Deployment {self.pk} - exam={self.exam.pk}, gen={self.cohort.pk}"
