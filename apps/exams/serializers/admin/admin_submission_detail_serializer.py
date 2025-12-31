from typing import Any

from rest_framework import serializers

from apps.exams.models import ExamDeployment
from apps.exams.models.exam_question import QuestionType
from apps.exams.models.exam_submission import ExamSubmission


class ExamInfoSerializer(serializers.ModelSerializer[ExamDeployment]):
    """시험 정보"""

    exam_title = serializers.CharField(source="exam.title", read_only=True)
    subject_name = serializers.CharField(source="exam.subject.title", read_only=True)

    class Meta:
        model = ExamDeployment
        fields = ["exam_title", "subject_name", "duration_time", "open_at", "close_at"]
        read_only_fields = fields


class StudentInfoSerializer(serializers.ModelSerializer[ExamSubmission]):
    """응시자 정보"""

    nickname = serializers.CharField(source="submitter.nickname", read_only=True)
    name = serializers.CharField(source="submitter.name", read_only=True)
    course_name = serializers.CharField(source="deployment.cohort.course.name", read_only=True)
    cohort_number = serializers.IntegerField(source="deployment.cohort.number", read_only=True)

    class Meta:
        model = ExamSubmission
        fields = ["nickname", "name", "course_name", "cohort_number"]
        read_only_fields = fields


class ResultInfoSerializer(serializers.ModelSerializer[ExamSubmission]):
    """시험 결과 정보"""

    total_question_count = serializers.SerializerMethodField(read_only=True)
    elapsed_time = serializers.TimeField(read_only=True)

    class Meta:
        model = ExamSubmission
        fields = ["score", "correct_answer_count", "total_question_count", "cheating_count", "elapsed_time"]
        read_only_fields = fields

    def get_total_question_count(self, obj: ExamSubmission) -> int:
        return len(obj.deployment.questions_snapshot)


class QuestionDetailSerializer(serializers.Serializer[dict[str, Any]]):
    """문제 풀이 내역"""

    id = serializers.IntegerField(read_only=True)
    number = serializers.IntegerField(read_only=True)
    type = serializers.ChoiceField(choices=QuestionType.choices, read_only=True)
    question = serializers.CharField(read_only=True)
    prompt = serializers.CharField(read_only=True)
    options = serializers.ListField(child=serializers.CharField(), read_only=True)
    point = serializers.IntegerField(read_only=True)
    answer = serializers.ListField(child=serializers.CharField(), read_only=True, help_text="문제 정답")
    submitted_answer = serializers.ListField(
        child=serializers.CharField(), read_only=True, help_text="사용자가 제출한 정답"
    )
    explanation = serializers.CharField(read_only=True)
    is_correct = serializers.BooleanField(read_only=True, help_text="문제를 맞혔는지 여부")


class ExamSubmissionDetailSerializer(serializers.ModelSerializer[ExamSubmission]):
    """쪽지시험 응시 내역 상세 조회 응답"""

    exam = ExamInfoSerializer(source="deployment", read_only=True)
    student = StudentInfoSerializer(source="*", read_only=True)
    result = ResultInfoSerializer(source="*", read_only=True)
    questions = QuestionDetailSerializer(source="merged_questions", many=True, read_only=True)

    class Meta:
        model = ExamSubmission
        fields = ["exam", "student", "result", "questions"]
        read_only_fields = fields
