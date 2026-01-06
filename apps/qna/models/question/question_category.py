from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel


class QuestionCategory(TimeStampedModel):
    CATEGORY_TYPES = (
        ("large", "대분류"),
        ("medium", "중분류"),
        ("small", "소분류"),
    )

    name = models.CharField(max_length=50, verbose_name="카테고리 이름")
    type = models.CharField(max_length=10, choices=CATEGORY_TYPES, default="large", verbose_name="카테고리 종류")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children", verbose_name="부모 카테고리"
    )

    class Meta:
        db_table = "question_categories"
        verbose_name = "질의응답 카테고리"
        verbose_name_plural = "질의응답 카테고리 목록"

    def __str__(self) -> str:
        return f"[{self.get_type_display()}] {self.name}"

    def clean(self) -> None:
        """계층 구조 유효성 검사"""
        if self.type == "large" and self.parent is not None:
            raise ValidationError({"parent": "대분류는 부모 카테고리를 가질 수 없습니다."})

        if self.type == "medium":
            if self.parent is None or self.parent.type != "large":
                raise ValidationError({"parent": "중분류의 부모는 [대분류]여야 합니다."})

        if self.type == "small":
            if self.parent is None or self.parent.type != "medium":
                raise ValidationError({"parent": "소분류의 부모는 [중분류]여야 합니다."})
