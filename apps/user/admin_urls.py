from django.urls import path

from apps.user.views.admin.accounts import (
    AdminAccountListAPIView,
    AdminAccountRetrieveUpdateView,
    AdminAccountRoleUpdateView,
)

urlpatterns = [
    path("accounts", AdminAccountListAPIView.as_view(), name="admin-account-list"),
    path("accounts/<int:account_id>", AdminAccountRetrieveUpdateView.as_view(), name="admin-account-detail"),
    path("accounts/<int:account_id>/role", AdminAccountRoleUpdateView.as_view(), name="admin-account-update-role"),
]
