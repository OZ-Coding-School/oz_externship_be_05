from django.urls import path

from apps.user.views.admin.accounts import (
    AdminAccountListAPIView,
    AdminAccountRetrieveUpdateView,
    AdminAccountRoleUpdateView,
)
from apps.user.views.admin.enrollments import (
    AdminStudentEnrollAcceptView,
    AdminStudentEnrollRejectView,
    AdminStudentsEnrollViews,
    AdminStudentView,
)

urlpatterns = [
    path("accounts", AdminAccountListAPIView.as_view(), name="admin-account-list"),
    path("accounts/<int:account_id>", AdminAccountRetrieveUpdateView.as_view(), name="admin-account-detail"),
    path("accounts/<int:account_id>/role", AdminAccountRoleUpdateView.as_view(), name="admin-account-update-role"),
    path("students", AdminStudentView.as_view(), name="admin-student-list"),
    path("students-enrollments", AdminStudentsEnrollViews.as_view(), name="admin-student-enrollments-list"),
    path(
        "students-enrollments/accept", AdminStudentEnrollAcceptView.as_view(), name="admin-student-enrollments-accept"
    ),
    path(
        "students-enrollments/reject", AdminStudentEnrollRejectView.as_view(), name="admin-student-enrollments-reject"
    ),
]
