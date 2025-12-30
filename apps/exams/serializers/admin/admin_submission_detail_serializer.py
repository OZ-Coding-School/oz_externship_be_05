from typing import Any

from rest_framework import serializers

from apps.exams.models.exam_submission import ExamSubmission
from apps.exams.services.admin.admin_submission_detail_services import (
    calculate_submission_elapsed_time,
)


class ExamInfoSerializer(serializers.Serializer[Any]):
    """시험 정보"""

    exam_title = serializers.CharField(source="deployment.exam.title")
    subject_name = serializers.CharField(source="deployment.exam.subject.title")
    duration_time = serializers.IntegerField(source="deployment.duration_time")
    open_at = serializers.SerializerMethodField()
    close_at = serializers.SerializerMethodField()

    def get_open_at(self, obj: ExamSubmission) -> str:
        return obj.deployment.open_at.strftime("%Y-%m-%d %H:%M:%S")

    def get_close_at(self, obj: ExamSubmission) -> str:
        return obj.deployment.close_at.strftime("%Y-%m-%d %H:%M:%S")


class StudentInfoSerializer(serializers.Serializer[Any]):
    """응시자 정보"""

    nickname = serializers.CharField(source="submitter.nickname")
    name = serializers.CharField(source="submitter.name")
    course_name = serializers.CharField(source="deployment.cohort.course.name")
    cohort_number = serializers.IntegerField(source="deployment.cohort.number")


class ResultInfoSerializer(serializers.Serializer[Any]):
    """시험 결과 정보"""

    score = serializers.IntegerField()
    correct_answer_count = serializers.IntegerField()
    total_question_count = serializers.SerializerMethodField()
    cheating_count = serializers.IntegerField()
    elapsed_time = serializers.SerializerMethodField()

    def get_total_question_count(self, obj: ExamSubmission) -> int:
        return len(obj.deployment.questions_snapshot)

    def get_elapsed_time(self, obj: ExamSubmission) -> int:
        return calculate_submission_elapsed_time(obj)


class QuestionDetailSerializer(serializers.Serializer[Any]):
    """문제 풀이 내역"""

    question_id = serializers.IntegerField()
    number = serializers.IntegerField()
    type = serializers.CharField()
    question = serializers.CharField()
    prompt = serializers.CharField(allow_null=True)
    options = serializers.ListField(
        child=serializers.CharField(),
        allow_null=True,
    )
    point = serializers.IntegerField()
    submitted_answer = serializers.JSONField()
    correct_answer = serializers.JSONField(source="answer")
    is_correct = serializers.BooleanField()
    explanation = serializers.CharField()


class ExamSubmissionDetailSerializer(serializers.ModelSerializer[ExamSubmission]):
    """쪽지시험 응시 내역 상세 조회 응답"""

    exam = ExamInfoSerializer(source="*")
    student = StudentInfoSerializer(source="*")
    result = ResultInfoSerializer(source="*")
    questions = serializers.SerializerMethodField()

    class Meta:
        model = ExamSubmission
        fields = ["exam", "student", "result", "questions"]

    def get_questions(self, obj: ExamSubmission) -> Any:
        # 뷰에서 비즈니스 로직(채점)이 완료된 데이터를 가져옴
        questions_data = self.context.get("questions_data", [])
        return QuestionDetailSerializer(questions_data, many=True).data
