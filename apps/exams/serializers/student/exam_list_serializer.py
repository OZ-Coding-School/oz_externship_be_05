from typing import Any, Optional

from rest_framework import serializers

from apps.courses.serializers.subject_serializer import SubjectSimpleSerializer
from apps.exams.models import Exam, ExamDeployment, ExamSubmission


class ExamSummarySerializer(serializers.ModelSerializer[Exam]):
    """시험 기본 정보 요약 (subject 포함)"""

    subject = SubjectSimpleSerializer()

    class Meta:
        model = Exam
        fields = ["id", "title", "subject", "thumbnail_img_url"]
        read_only_fields = fields


class ExamDeploymentListSerializer(serializers.ModelSerializer[ExamDeployment]):
    """수강생용 쪽지시험 목록 조회용 시리얼라이저"""

    exam = ExamSummarySerializer()

    submission_id = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()
    total_score = serializers.SerializerMethodField()
    exam_info = serializers.SerializerMethodField()
    is_done = serializers.SerializerMethodField()

    class Meta:
        model = ExamDeployment
        fields = [
            "id",
            "submission_id",
            "exam",
            "question_count",
            "total_score",
            "exam_info",
            "is_done",
            "duration_time",
        ]
        read_only_fields = fields

    def _get_submission(self, obj: ExamDeployment) -> Optional[ExamSubmission]:
        """View에서 Prefetch(to_attr='user_submission_list')로 주입한 데이터를 가져옴"""
        submissions = getattr(obj, "user_submission_list", [])
        return submissions[0] if submissions else None

    def get_submission_id(self, obj: ExamDeployment) -> Optional[int]:
        """제출 내역 ID 반환 (없으면 null)"""
        submission = self._get_submission(obj)
        return submission.id if submission else None

    def get_question_count(self, obj: ExamDeployment) -> int:
        """스냅샷이 있으면 스냅샷 개수, 없으면 관련 질문 개수 반환"""
        if obj.questions_snapshot:
            return len(obj.questions_snapshot)
        return obj.exam.questions.count()

    def get_total_score(self, obj: ExamDeployment) -> int:
        """배포 시점의 스냅샷 점수 합계 또는 현재 시험 문항 점수 합계 반환"""
        if obj.questions_snapshot:
            return sum(q.get("point", 0) for q in obj.questions_snapshot)
        # 쿼리셋 최적화를 위해 aggregate 사용을 권장하나, 여기서는 필드 로직을 유지합니다.
        return sum(q.point for q in obj.exam.questions.all())

    def get_exam_info(self, obj: ExamDeployment) -> dict[str, Any]:
        """응시 정보(상태, 점수, 정답 개수) 매핑"""
        submission = self._get_submission(obj)
        return {
            "status": "done" if submission else "pending",
            "score": submission.score if submission else None,
            "correct_answer_count": submission.correct_answer_count if submission else None,
        }

    def get_is_done(self, obj: ExamDeployment) -> bool:
        """응시 완료 여부 (Boolean)"""
        return self._get_submission(obj) is not None
