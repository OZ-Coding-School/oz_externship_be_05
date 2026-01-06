from django.utils import timezone

from apps.core.exceptions.exception_messages import EMS
from apps.core.exceptions.exceptions import GoneException, LockedException
from apps.exams.models import ExamDeployment, ExamSubmission


def validate_exam_access(deployment: ExamDeployment, submission: ExamSubmission | None) -> None:
    """
    시험 접근 가능 여부 검증
    - GoneException: 시험이 이미 종료된 경우
    - LockedException: 아직 응시할 수 없는 경우
    """
    now = timezone.now()

    # 아직 시작 전인지 확인
    if deployment.open_at and now < deployment.open_at:
        raise LockedException(EMS.E423_LOCKED("응시")["error_detail"])

    # 이미 종료된 시험인지 확인
    if deployment.close_at and now > deployment.close_at:
        raise GoneException(EMS.E410_ENDED("시험")["error_detail"])


def calculate_elapsed_time(submission: ExamSubmission | None) -> int:
    """
    경과 시간 계산 (초 단위)
    """
    if not submission or not submission.started_at:
        return 0

    now = timezone.now()
    elapsed = (now - submission.started_at).total_seconds()
    return int(elapsed)
