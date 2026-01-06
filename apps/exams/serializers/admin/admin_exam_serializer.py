from rest_framework import serializers

from apps.courses.serializers.subject_serializer import SubjectSimpleSerializer
from apps.exams.models import Exam
from apps.exams.serializers.admin.admin_question_serializer import (
    ExamQuestionDetailSerializer,
)


class AdminExamSerializer(serializers.ModelSerializer[Exam]):
    """
    쪽지시험 생성(POST) 및 수정(PUT) 시 사용하는 시리얼라이저입니다.
    """

    subject_id = serializers.IntegerField(required=True)
    # SerializerMethodField 대신 CharField + source 사용 (Swagger 반영 및 N+1 방지)
    subject_name = serializers.CharField(source="subject.title", read_only=True)
    thumbnail_img = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "subject_id",
            "subject_name",
            "thumbnail_img",
            "thumbnail_img_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "subject_name", "created_at", "updated_at"]


class AdminExamListSerializer(serializers.ModelSerializer[Exam]):
    """
    GET /api/v1/admin/exams 요청 시 사용되는 목록 조회 시리얼라이저입니다.
    subject_name: subject.title
    question_count: 문제갯수(ExamQuestion)
    submit_count: 응시(제출)된 건수(ExamSubmission)
    """

    detail_url = serializers.CharField(source="thumbnail_img_url", read_only=True)
    subject_name = serializers.CharField(source="subject.title", read_only=True)  # subject

    # annotate로 추가된 필드를 IntegerField로 정의 (성능 향상)
    question_count = serializers.IntegerField(read_only=True)  # 시험에 포함된 문제 수
    submit_count = serializers.IntegerField(read_only=True)  # 총 응시된 건수

    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "subject_name",  # subject title
            "question_count",  # get_question_count
            "submit_count",  # get_submit_count
            "created_at",
            "updated_at",
            "detail_url",
        ]


class AdminExamQuestionsListSerializer(serializers.ModelSerializer[Exam]):
    """
    관리자용 쪽지시험 상세 조회 시리얼라이저입니다.
    GET /api/v1/admin/exams/{exam_id} 요청 시 사용됩니다.
    과목 정보와 포함된 모든 문제 상세 정보를 포함합니다.
    """

    subject = SubjectSimpleSerializer(read_only=True)  # subject 정보를 'subject_name'이 아니라 객체(depth)로 표현
    questions = ExamQuestionDetailSerializer(many=True, read_only=True)

    # annotate로 추가된 필드를 IntegerField로 정의 (성능 향상)
    # question_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Exam
        fields = [
            "id",  # Exam PK
            "title",  # Exam Title
            "subject",  # 과목정보 리스트 (SubjectSimpleSerializer 결과)
            "questions",  # 문제 상세 리스트 (ExamQuestionDetailSerializer 결과)
            "thumbnail_img_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
