from rest_framework import serializers

from apps.exams.models import Exam, ExamDeployment, ExamQuestion, ExamSubmission


class ExamSerializer(serializers.ModelSerializer):
    """
    POST, PUT, GET (x단일 조회x) 요청 시 사용되는 기본 시리얼라이저입니다.
    """

    exam_title = serializers.CharField(source="title", max_length=50)
    subject_id = serializers.IntegerField(required=True)
    subject_title = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = ["id", "subject_id", "subject_title", "exam_title", "thumbnail_img_url", "created_at", "updated_at"]
        read_only_fields = ["id", "subject_title", "created_at", "updated_at"]

    @staticmethod
    def get_subject_title(obj: Exam) -> str:
        """
        :param obj: Exam
        :return:(str) Subject의 title을 반환
        """
        return obj.subject.title


class ExamListSerializer(serializers.ModelSerializer):
    """
    GET /api/v1/admin/exams 요청 시 사용되는 목록 조회 시리얼라이저입니다.
    subject_name: subject_id
    question_count: 문제갯수(ExamQuestion)
    submit_count: 응시(제출)된 건수(ExamSubmission)
    """

    exam_title = serializers.CharField(source="title", read_only=True)
    subject_name = serializers.CharField(source="subject.title", read_only=True)  # subject
    question_count = serializers.SerializerMethodField()  # 시험에 포함된 문제 수
    submit_count = serializers.SerializerMethodField()  # 총 응시된 건수

    class Meta:
        model = Exam
        fields = [
            "id",
            "exam_title",
            "subject_id",
            "subject_name",     # subject title
            "question_count",   # get_question_count
            "submit_count",     # get_submit_count
            "created_at",
            "updated_at",
        ]

    @staticmethod
    def get_question_count(obj: Exam) -> int:
        """
        :param obj: Exam
        :return: (int) 해당 시험(Exam)에 연결된 문제(ExamQuestion)의 개수를 반환합니다.
        """
        return obj.questions.count()

    @staticmethod
    def get_submit_count(obj: Exam) -> int:
        """
        :param obj: Exam
        :return: (int)시험 배포(ExamDeployment)를 거쳐 총 제출(ExamSubmission)된 건수를 반환합니다.
        """
        count = 0
        # obj.deployments 해당 시험에 배포된 모든 인스턴스를 가져옵니다.
        for deployment in obj.deployments.all():
            count += deployment.submissions.count()
        return count
