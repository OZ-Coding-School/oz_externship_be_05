from typing import Optional

from rest_framework import serializers

from apps.qna.models import Question, QuestionCategory
from apps.user.models import RoleChoices, User


def validate_question_create_permission(user: User) -> None:
    if user.role != RoleChoices.ST:
        raise serializers.ValidationError({"type": "permission_denied"})


def validate_question_title_unique(title: Optional[str]) -> None:
    if not title:
        return

    if Question.objects.filter(title=title).exists():
        raise serializers.ValidationError({"type": "title_conflict"})


def validate_question_category(category_id: int | None) -> None:
    """
    카테고리 검증
    - None / 누락 → invalid_request 400
    - 존재하지 않는 PK → category_not_found 404
    """
    if category_id is None:
        raise serializers.ValidationError({"type": "invalid_request"})

    if not QuestionCategory.objects.filter(id=category_id).exists():
        raise serializers.ValidationError({"type": "category_not_found"})
