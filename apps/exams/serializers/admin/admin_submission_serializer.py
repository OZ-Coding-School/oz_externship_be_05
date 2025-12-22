from __future__ import annotations

from rest_framework import serializers

from apps.exams.models import ExamSubmission


class AdminSubmissionListSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """
    관리자 응시내역 목록의 '행(row)' 하나를 표현하는 serializer.
    (ExamSubmission 1건)
    """

    submission_id = serializers.IntegerField(source="id", read_only=True)

    # 사용자 정보
    nickname = serializers.CharField(source="submitter.nickname")
    name = serializers.CharField(source="submitter.name")

    # 과정 / 기수
    course_name = serializers.CharField(source="deployment.cohort.course.name")
    cohort_number = serializers.IntegerField(source="deployment.cohort.number")

    # 시험 정보
    exam_title = serializers.CharField(source="deployment.exam.title")
    subject_name = serializers.CharField(source="deployment.exam.subject.name", read_only=True)

    # 시간 정보
    started_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    finished_at = serializers.DateTimeField(
        source="created_at",
        format="%Y-%m-%d %H:%M:%S",
    )

    class Meta:
        model = ExamSubmission
        fields = (
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
        )
        # 관리자 조회 전용 응답이므로 전체 read-only
        read_only_fields = fields


class AdminExamSubmissionListSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """
    관리자 응시내역 목록 응답 wrapper.
    payload(dict) 그대로 감싸서 내려준다.
    """

    page = serializers.IntegerField()
    size = serializers.IntegerField()
    total_count = serializers.IntegerField()
    submissions = AdminSubmissionListSerializer(many=True)
