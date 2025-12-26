from apps.exams.views.admin.admin_deployment_view import (
    AdminDeploymentDetailUpdateDeleteView,
    DeploymentListCreateAPIView,
    ExamDeploymentStatusAPIView,
)
from apps.exams.views.admin.admin_exam_view import (
    ExamAdminListCreateAPIView,
    ExamAdminRetrieveUpdateDestroyAPIView,
)
from apps.exams.views.admin.admin_question_view import (
    ExamAdminQuestionUpdateDestroyAPIView,
)

# from .admin_question_view import
# from .admin_submission_view import

__all__ = [
    "ExamAdminListCreateAPIView",
    "ExamAdminRetrieveUpdateDestroyAPIView",
    "DeploymentListCreateAPIView",
    "AdminDeploymentDetailUpdateDeleteView",
    "ExamDeploymentStatusAPIView",
    "ExamAdminQuestionUpdateDestroyAPIView",
]
