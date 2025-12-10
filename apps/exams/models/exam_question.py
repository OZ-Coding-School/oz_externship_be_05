from django.db import models

from ...core.models import TimeStampedModel


class QuestionType(models.TextChoices):
    SINGLE_CHOICE = "single_choice", "단일 선택"
    MULTIPLE_CHOICE = "multiple_choice", "다중 선택"
    OX = "ox", "O/X"
    SHORT_ANSWER = "short_answer", "단답형"
    ORDERING = "ordering", "순서 정렬"
    FILL_BLANK = "fill_blank", "빈칸 채우기"


class ExamQuestion(TimeStampedModel):
    """
    시험 문항
    ERD: exam_questions
    """

    # ERD: exam_id bigint [not null]
    exam = models.ForeignKey(
        "exams.Exam",
        on_delete=models.CASCADE,
        related_name="questions",
    )

    # ERD: question varchar(255) [not null]
    question = models.CharField(max_length=255)

    # ERD: prompt text // 빈칸 채우기에 사용될 지문
    prompt = models.TextField(blank=True, null=True)

    # ERD: blank_count tinyint(1)
    blank_count = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        help_text="빈칸 채우기 문제의 빈칸 개수",
    )

    # ERD: options_json text
    # Postgres 사용이므로 JSONField로 매핑, 컬럼명은 options_json 유지
    options = models.JSONField(
        db_column="options_json",
        blank=True,
        null=True,
        help_text="객관식/순서정렬/OX 선택지 리스트",
    )

    # ERD: type enum [not null] // 문제유형
    type = models.CharField(
        max_length=32,
        choices=QuestionType.choices,
    )

    # ERD: answer json [not null] // 정답
    answer = models.JSONField(
        help_text="정답 표현 (문제 유형에 따라 문자열/리스트 등)",
    )

    # ERD: point tinyint(2) [not null] // 배점
    point = models.PositiveSmallIntegerField()

    # ERD: explanation text [not null] // 해설
    # 해설을 옵션으로 둘 수도 있어서 blank 허용
    explanation = models.TextField(
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "exam_questions"
        verbose_name = "Exam Question"
        verbose_name_plural = "Exam Questions"

    def __str__(self) -> str:
        return f"[{self.exam.pk}] {self.question[:30]}"
