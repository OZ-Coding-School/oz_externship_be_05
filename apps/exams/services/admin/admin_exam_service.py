from typing import Any, Dict

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import QuerySet

from apps.exams.models import Exam


class ExamService:
    """
    쪽지시험(Exam)에 대한 비즈니스 로직을 처리합니다.
    """

    def get_exam_list(self) -> QuerySet[Exam]:
        """
        시험 목록 조회를 위한 쿼리셋을 반환합니다.
        """
        return Exam.objects.all()  # 데이터 접근 로직의 시작점

    @transaction.atomic
    def create_exam(self, validated_data: Dict[str, Any]) -> Exam:
        """
        쪽지시험을 생성합니다.
        """
        exam = Exam.objects.create(**validated_data)
        return exam

    @transaction.atomic
    def update_exam(self, exam_id: int, validated_data: Dict[str, Any]) -> Exam:
        """
        쪽지시험을 수정합니다.
        """
        try:
            exam = Exam.objects.get(pk=exam_id)
        except ObjectDoesNotExist:
            raise ValueError(f"Exam with ID {exam_id} not found.")

        # 데이터 업데이트
        for key, value in validated_data.items():
            setattr(exam, key, value)

        exam.save()
        return exam

    @transaction.atomic
    def delete_exam(self, exam_id: int) -> None:
        """
        쪽지시험을 삭제합니다.
        """
        try:
            exam = Exam.objects.get(pk=exam_id)
        except ObjectDoesNotExist:
            raise ValueError(f"Exam with ID {exam_id} not found.")

        exam.delete()
