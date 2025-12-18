from typing import Any, Dict, Optional

from django.db import transaction
from django.db.models import Count, QuerySet

from apps.core.constants import VALID_SORT_FIELDS
from apps.courses.models import Subject
from apps.exams.models import Exam


class ExamService:
    """쪽지시험(Exam) 관련 비즈니스 로직을 처리하는 서비스 계층."""

    # ----------------------------------------------------------------------
    # READ(조회)
    # ----------------------------------------------------------------------
    def get_exam_list(self) -> QuerySet[Exam]:
        """
        기본 쿼리셋(전체) 반환합니다.
        집계 필드를 미리 계산(annotate)합니다.
        """
        return Exam.objects.annotate(
            question_count=Count("questions", distinct=True),
            # Exam -> Deployment -> Submission 경로의 개수 집계
            submit_count=Count("deployments__submissions", distinct=True),
        )

    def get_exam_by_id(self, exam_id: int) -> Exam:
        """
        ID로 쪽지시험 객체를 조회합니다.
        """
        return self.get_exam_list().select_related("subject").get(pk=exam_id)

    def get_subject_by_id(self, subject_id: int) -> Subject:
        return Subject.objects.get(pk=subject_id)

    # ----------------------------------------------------------------------
    # 필터 및 정렬
    # ----------------------------------------------------------------------
    def apply_filters_and_sorting(self, queryset: QuerySet[Exam], query_params: Dict[str, Any]) -> QuerySet[Exam]:
        """
        필터링, 정렬을 적용한 쿼리셋을 반환합니다.
        :param queryset: 정렬할 쿼리셋
        :param query_params: 명시적인 검색/정렬 파라미터와 '_id'로 끝나는 필터만 적용
        :return: QuerySet
        """
        # 필터링
        search_keyword: Optional[str] = query_params.get("search_keyword")
        sort_field: Optional[str] = query_params.get("sort")
        order: str = query_params.get("order", "desc")

        # 검색어 필터링
        if search_keyword:
            queryset = queryset.filter(
                title__icontains=search_keyword
            )  # Exam 모델의 대소문자무시(i) search_keyword포함 제목 필터링

        # id값 필터링 ex) subject_id
        for key, value in query_params.items():
            if key.endswith("_id") and value:
                try:
                    queryset = queryset.filter(**{key: value})  # 변수를 필드명으로 사용하기위한 언패킹(**)
                except (ValueError, TypeError):
                    continue

        # 정렬
        if sort_field is None or sort_field not in VALID_SORT_FIELDS:
            sort_field = "created_at"
            order = "desc"

        order_prefix: str = "-" if order == "desc" else ""
        return queryset.order_by(f"{order_prefix}{sort_field}")

    # ----------------------------------------------------------------------
    # CREATE(생성)
    # ----------------------------------------------------------------------
    def create_exam(self, validated_data: Dict[str, Any]) -> Exam:
        """
        새로운 쪽지시험을 생성합니다.
        """
        # subject_id(FK) 존재 여부 확인
        subject_id = validated_data.pop("subject_id")
        subject_instance = self.get_subject_by_id(subject_id)

        # Exam 생성. 로직 추가시 atomic 추가 권장.
        exam = Exam.objects.create(subject=subject_instance, **validated_data)
        return exam

    # ----------------------------------------------------------------------
    # UPDATE(수정)
    # ----------------------------------------------------------------------
    def update_exam(self, exam: Exam, validated_data: Dict[str, Any]) -> Exam:
        """
        기존 쪽지시험 인스턴스의 필드를 업데이트하고 저장합니다.

        args:
            exam: 업데이트할 Exam 인스턴스 (이미 뷰에서 조회됨)
            validated_data: 시리얼라이저를 통과한 데이터
        """
        subject_id = validated_data.pop("subject_id")

        with transaction.atomic():
            if subject_id is not None:
                # subject_id 존재 여부 확인
                subject_instance = self.get_subject_by_id(subject_id)
                exam.subject = subject_instance

            # 나머지  데이터 필드 업데이트
            for key, value in validated_data.items():
                setattr(exam, key, value)

            exam.save()
            return exam

    # ----------------------------------------------------------------------
    # DELETE(삭제)
    # ----------------------------------------------------------------------
    def delete_exam(self, exam_id: int) -> None:
        """
        지정된 ID의 쪽지시험을 삭제합니다.
        """
        # 뷰에서 PK 포맷 검증을 이미 수행했으므로, 여기서는 Exam 객체 존재 여부만 확인합니다.
        exam_to_delete = self.get_exam_by_id(exam_id)
        exam_to_delete.delete()
