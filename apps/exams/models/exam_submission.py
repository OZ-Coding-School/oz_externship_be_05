from django.conf import settings
from django.db import models

from ...core.models import TimeStampedModel


class ExamSubmission(TimeStampedModel):
    """
    시험 응시/제출 내역
    ERD: exam_submissions
    """

    # ERD: submitter_id bigint [not null]
    submitter = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="exam_submissions",
    )

    # ERD: deployment_id bigint [not null]
    deployment = models.ForeignKey(
        "exams.ExamDeployment",
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    # ERD: started_at datetime [not null]
    started_at = models.DateTimeField()

    # ERD: cheating_count tinyint(1) [not null]
    cheating_count = models.PositiveSmallIntegerField(default=0)

    # ERD: answers_json json [not null]
    answers = models.JSONField(
        db_column="answers_json",
        help_text="제출한 답안 전체(JSON)",
    )

    # ERD: score tinyint [not null]
    score = models.PositiveSmallIntegerField()

    # ERD: correct_answer_count tinyint [not null]
    correct_answer_count = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "exam_submissions"
        verbose_name = "Exam Submission"
        verbose_name_plural = "Exam Submissions"
        indexes = [
            models.Index(fields=["deployment", "submitter"]),
        ]

    def __str__(self) -> str:
        return f"Submission {self.pk} by {self.submitter.pk} on deployment {self.deployment.pk}"