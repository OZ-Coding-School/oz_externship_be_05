from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.core.exceptions.exception_messages import EMS
from apps.exams.models.exam_submission import ExamSubmission


class IsSubmissionOwner(BasePermission):
    """
    ExamSubmission의 submitter 본인만 접근 가능
    """

    message = EMS.E403_QUIZ_PERMISSION_DENIED("조회")

    def has_object_permission(
        self,
        request: Request,
        view: APIView,
        obj: ExamSubmission,
    ) -> bool:
        return obj.submitter_id == request.user.id
