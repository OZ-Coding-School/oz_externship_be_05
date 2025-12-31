from django.urls import path

from apps.user.views.admin.accounts import (
    AdminAccountListAPIView,
    AdminAccountRetrieveUpdateView,
    AdminAccountRoleUpdateView,
)
from apps.user.views.admin.analytics import (
    AdminSignupStatsAPIView,
    AdminWithdrawalStatsAPIView,
)
from apps.user.views.admin.enrollments import (
    AdminStudentEnrollAcceptView,
    AdminStudentEnrollRejectView,
    AdminStudentsEnrollViews,
    AdminStudentView,
)
from apps.user.views.admin.withdrawal import (
    AdminAccountWithdrawalListAPIView,
    AdminAccountWithdrawalRetrieveDestroyAPIView,
)

urlpatterns = [
    path("accounts", AdminAccountListAPIView.as_view(), name="admin-account-list"),
    path("accounts/<int:account_id>", AdminAccountRetrieveUpdateView.as_view(), name="admin-account-detail"),
    path("accounts/<int:account_id>/role", AdminAccountRoleUpdateView.as_view(), name="admin-account-update-role"),
    path("students", AdminStudentView.as_view(), name="admin-student-list"),
    path("student-enrollments", AdminStudentsEnrollViews.as_view(), name="admin-student-enrollments-list"),
    path("student-enrollments/accept", AdminStudentEnrollAcceptView.as_view(), name="admin-student-enrollments-accept"),
    path("student-enrollments/reject", AdminStudentEnrollRejectView.as_view(), name="admin-student-enrollments-reject"),
    path("withdrawals", AdminAccountWithdrawalListAPIView.as_view()),
    path("withdrawals/<withdrawal_id>", AdminAccountWithdrawalRetrieveDestroyAPIView.as_view()),
    path("analytics/signup/trends", AdminSignupStatsAPIView.as_view(), name="admin-analytics-signup-trends"),
    path(
        "analytics/withdrawals/trends", AdminWithdrawalStatsAPIView.as_view(), name="admin-analytics-withdrawals-trends"
    ),
]
