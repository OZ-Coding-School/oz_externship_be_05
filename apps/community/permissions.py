from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.community.models.post import Post


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    게시글 작성자만 수정/삭제 가능, 그 외에는 읽기만 가능
    """

    SAFE_METHOD = "GET"

    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method == self.SAFE_METHOD:
            return True

        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: APIView, obj: Post) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.author == request.user
