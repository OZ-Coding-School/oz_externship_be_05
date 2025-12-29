from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from apps.core.exceptions.exception_messages import EMS
from apps.core.exceptions.exceptions import LockedException
from apps.exams.models import ExamDeployment


class ExamAccessCodeService:
    """
    시험 참가코드 검증 서비스
    """

    @staticmethod
    def verify_access_code(deployment_id: int, access_code: str) -> None:

        # 배포 존재 여부 확인
        deployment = ExamAccessCodeService._get_deployment(deployment_id)

        # 응시 가능 시간 확인
        ExamAccessCodeService._check_available_time(deployment)

        # 참가 코드 검증
        ExamAccessCodeService._validate_access_code(deployment, access_code)

    # ---------------------------------------
    @staticmethod
    def _get_deployment(deployment_id: int) -> ExamDeployment:
        """배포 정보 조회"""
        try:
            return ExamDeployment.objects.get(id=deployment_id)
        except ExamDeployment.DoesNotExist:
            raise NotFound(detail=EMS.E404_NOT_FOUND("배포 정보")["error_detail"])

    @staticmethod
    def _check_available_time(deployment: ExamDeployment) -> None:
        """응시 가능 시간 확인"""
        now = timezone.now()

        # open_at이 있고, 아직 시작 시간 전인 경우
        if deployment.open_at and now < deployment.open_at:
            raise LockedException(EMS.E423_LOCKED("응시")["error_detail"])

        # close_at이 있고, 이미 종료 시간이 지난 경우
        if deployment.close_at and now > deployment.close_at:
            raise LockedException(error_detail="시험 응시 시간이 지났습니다.")

    @staticmethod
    def _validate_access_code(deployment: ExamDeployment, input_code: str) -> None:
        """참가 코드 검증"""

        if input_code != deployment.access_code:
            raise ValidationError(EMS.E400_EXAM_CODE_MISMATCH["error_detail"])
