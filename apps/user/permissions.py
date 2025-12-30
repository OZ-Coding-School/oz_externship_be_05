from typing import Any

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.user.models.user import RoleChoices

ADMIN_STAFF_ROLES = {
    RoleChoices.AD, 
    RoleChoices.TA, 
    RoleChoices.LC, 
    RoleChoices.OM, 
}


class IsAdminStaffRole(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        role = getattr(user, "role", None)
        return role in ADMIN_STAFF_ROLES


class AdminAccountRoleUpdatePayloadPermission(BasePermission):

    def has_permission(self, request: Request, view: APIView) -> bool:
        data: dict[str, Any] = request.data

        role = data.get("role")
        cohort_id_present = ("cohort_id" in data) and (data.get("cohort_id") is not None)
        courses_present = ("assigned_courses" in data) and (data.get("assigned_courses") is not None)

        if role in (RoleChoices.USER, RoleChoices.AD):
            if cohort_id_present or courses_present:
                raise PermissionDenied({"detail": "USER/ADMIN은 role만 변경 가능합니다.", "allowed_fields": ["role"]})
            return True

        if role in (RoleChoices.TA, RoleChoices.ST):
            if not cohort_id_present:
                raise PermissionDenied({"cohort_id": ["학생/조교 권한으로 변경 시 필수 필드입니다."]})
            if courses_present:
                raise PermissionDenied({"assigned_courses": ["학생/조교 권한으로 변경할 수 없는 필드입니다."]})
            return True

        if role in (RoleChoices.OM, RoleChoices.LC):
            if not courses_present:
                raise PermissionDenied({"assigned_courses": ["러닝코치/운영매니저 권한으로 변경 시 필수 필드입니다."]})
            if cohort_id_present:
                raise PermissionDenied({"cohort_id": ["러닝코치/운영매니저 권한으로 변경할 수 없는 필드입니다."]})
            return True

        return True

