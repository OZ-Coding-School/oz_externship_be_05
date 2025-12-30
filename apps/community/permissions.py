from typing import Any

from rest_framework import permissions
from rest_framework.request import Request

from apps.community.models.post import Post


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    게시글 작성자만 수정/삭제 가능, 그 외에는 읽기만 가능
    """

    def has_object_permission(self, request: Request, view: Any, obj: Post) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.author == request.user
