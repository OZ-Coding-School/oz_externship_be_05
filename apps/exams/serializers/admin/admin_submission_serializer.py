from __future__ import annotations

from rest_framework import serializers

from apps.exams.models import ExamSubmission


class AdminSubmission(serializers.ModelSerializer):  # type: ignore[type-arg]
    submission_id = serializers.IntegerField(source="id", read_only=True)

    nickname = serializers.CharField(source="submitter.nickname", read_only=True)
    name = serializers.CharField(source="submitter.name", read_only=True)

    course_name = serializers.CharField(source="deployment.cohort.course.name", read_only=True)
    cohort_number = serializers.IntegerField(source="deployment.cohort.number", read_only=True)

    exam_title = serializers.CharField(source="deployment.exam.title", read_only=True)
    subject_name = serializers.CharField(source="deployment.exam.subject.name", read_only=True)

    score = serializers.IntegerField(read_only=True)
    cheating_count = serializers.IntegerField(read_only=True)

    started_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    # finished_at > submit - created_at
    finished_at = serializers.DateTimeField(source="created_at", format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = ExamSubmission
        fields = [
            "submission_id",
            "nickname",
            "name",
            "course_name",
            "cohort_number",
            "exam_title",
            "subject_name",
            "score",
            "cheating_count",
            "started_at",
            "finished_at",
        ]


class AdminExamSubmissionList(serializers.Serializer):  # type: ignore[type-arg]
    page = serializers.IntegerField()
    size = serializers.IntegerField()
    total_count = serializers.IntegerField()
    submissions = AdminSubmission(many=True)
