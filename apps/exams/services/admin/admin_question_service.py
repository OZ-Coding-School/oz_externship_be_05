from typing import Any, Optional

from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import NotFound, ValidationError

from apps.exams.models import Exam, ExamQuestion


class AdminQuestionService:
    def _check_limits(self, exam_id: int, added_point: int, exclude_question_id: Optional[int] = None) -> None:
        """문제 수(20개) 및 총 배점(100점) 상한선 검증"""
        # select_for_update()를 사용하여 검증 중 데이터 변경 방지
        query = ExamQuestion.objects.select_for_update().filter(exam_id=exam_id)

        # 문제 수 체크 (생성 시에만)
        if exclude_question_id is None:
            if query.count() >= 20:
                raise ValidationError()  # 409

        # 총 배점 체크
        if exclude_question_id:
            query = query.exclude(id=exclude_question_id)

        current_total = query.aggregate(Sum("point"))["point__sum"] or 0
        if current_total + added_point > 100:
            raise ValidationError()

    @transaction.atomic
    def create_question(self, exam_id: int, validated_data: dict[str, Any]) -> ExamQuestion:
        # 시험 존재 여부 확인 (404 대응)
        try:
            Exam.objects.select_for_update().get(id=exam_id)
        except Exam.DoesNotExist:
            raise NotFound()

        self._check_limits(exam_id, validated_data.get("point", 0))
        return ExamQuestion.objects.create(exam_id=exam_id, **validated_data)
