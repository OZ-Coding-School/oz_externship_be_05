from rest_framework import serializers

from apps.exams.models import Exam


class ExamSerializer(serializers.ModelSerializer[Exam]):
    """
    POST, PUT, GET (x단일 조회x) 요청 시 사용되는 기본 시리얼라이저입니다.
    """

    exam_title = serializers.CharField(source="title", max_length=50)
    subject_id = serializers.IntegerField(required=True)
    # SerializerMethodField 대신 CharField + source 사용 (Swagger 반영 및 N+1 방지)
    subject_title = serializers.CharField(source="subject.title", read_only=True)

    class Meta:
        model = Exam
        fields = ["id", "subject_id", "subject_title", "exam_title", "thumbnail_img_url", "created_at", "updated_at"]
        read_only_fields = ["id", "subject_title", "created_at", "updated_at"]


class ExamListSerializer(serializers.ModelSerializer[Exam]):
    """
    GET /api/v1/admin/exams 요청 시 사용되는 목록 조회 시리얼라이저입니다.
    subject_name: subject_id
    question_count: 문제갯수(ExamQuestion)
    submit_count: 응시(제출)된 건수(ExamSubmission)
    """

    exam_title = serializers.CharField(source="title", read_only=True)
    subject_name = serializers.CharField(source="subject.title", read_only=True)  # subject

    # annotate로 추가된 필드를 IntegerField로 정의 (성능 향상)
    question_count = serializers.IntegerField(read_only=True)  # 시험에 포함된 문제 수
    submit_count = serializers.IntegerField(read_only=True)  # 총 응시된 건수

    class Meta:
        model = Exam
        fields = [
            "id",
            "exam_title",
            "subject_id",
            "subject_name",  # subject title
            "question_count",  # get_question_count
            "submit_count",  # get_submit_count
            "created_at",
            "updated_at",
        ]
