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

    def _get_question_select_lock(self, question_id: int) -> ExamQuestion:
        """객체 조회 및 락 전용 메서드."""
        try:
            return ExamQuestion.objects.select_for_update().get(id=question_id)
        except ExamQuestion.DoesNotExist:
            raise NotFound()

    @transaction.atomic
    def update_question(self, question_id: int, validated_data: dict[str, Any]) -> ExamQuestion:

        question = self._get_question_select_lock(question_id)

        # 점수 수정이 포함된 경우에만 제한 검사
        if "point" in validated_data:
            self._check_limits(question.exam_id, validated_data["point"], exclude_question_id=question_id)

        for attr, value in validated_data.items():
            setattr(question, attr, value)

        question.save()
        return question

    @transaction.atomic
    def delete_question(self, question_id: int) -> None:
        try:
            question_to_delete = self._get_question_select_lock(question_id)
            question_to_delete.delete()
        except ExamQuestion.DoesNotExist:
            raise NotFound()
