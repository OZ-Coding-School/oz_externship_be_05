from django.urls import path

from apps.user.views.admin.accounts import AdminAccountListAPIView

urlpatterns = [
    path("admin/accounts", AdminAccountListAPIView.as_view(), name="admin-account-list"),
]
