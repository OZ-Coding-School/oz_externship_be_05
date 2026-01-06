from __future__ import annotations

from typing import Any

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.user.models.user import RoleChoices


class AnswerAccessPermission(permissions.BasePermission):
    """
    [작성 권한 - 공통]
    - answer/comment 도메인 접근자체허용여부
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        # 안전하게 role 가져오기
        user_role = getattr(request.user, "role", None)

        allowed_roles = {
            RoleChoices.TA,
            RoleChoices.LC,
            RoleChoices.OM,
            RoleChoices.ST,
            RoleChoices.AD,
        }

        return user_role in allowed_roles


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    [수정/삭제 권한]
    - 작성자(author) 본인만 수정/삭제 가능
    """

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True

        # obj.author와 request.user 비교
        obj_author = getattr(obj, "author", None)
        return obj_author == request.user


class IsQuestionAuthor(permissions.BasePermission):
    """
    [채택 권한]
    - 이 답변이 달린 '질문(Question)'의 작성자만이 접근 가능
    - 채택 API 뷰에서 사용됨
    """

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        # obj는 Answer 인스턴스입니다.
        # Answer -> Question -> Author 로 타고 올라가서 확인해야 합니다.
        if not hasattr(obj, "question"):
            return False

        return bool(obj.question.author == request.user)
