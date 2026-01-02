from __future__ import annotations

from unittest.mock import MagicMock, Mock

from django.test import SimpleTestCase

from apps.qna.permissions.answer.answer_permission import (
    AnswerAccessPermission,
    IsOwnerOrReadOnly,
    IsQuestionAuthor,
)
from apps.user.models.user import RoleChoices

"""
Answer 권한 테스트
- AnswerAccessPermission
- IsOwnerOrReadOnly
- IsQuestionAuthor
"""

"""
test_unauthenticated_user_denied
    비인증 유저 접근 불가
test_user_without_role_denied
    role이 없는 유저는 접근 불가
test_allowed_roles_granted
    허용된 역할은 접근 가능
def test_invalid_role_denied
    허용되지 않은 역할은 접근 불가

"""


class TestAnswerAccessPermission(SimpleTestCase):
    def setUp(self) -> None:
        self.mock_view = MagicMock()
        self.mock_request = Mock()
        self.mock_request.method = "GET"

    @staticmethod
    def _user_with_role(role: RoleChoices) -> Mock:
        user = Mock()
        user.is_authenticated = True
        user.role = role
        return user

    def test_unauthenticated_user_denied(self) -> None:
        user = Mock()
        user.is_authenticated = False
        self.mock_request.user = user

        permission = AnswerAccessPermission()
        result = permission.has_permission(self.mock_request, self.mock_view)

        self.assertFalse(result)

    def test_user_without_role_denied(self) -> None:
        user = Mock()
        user.is_authenticated = True
        user.role = None
        self.mock_request.user = user

        permission = AnswerAccessPermission()
        result = permission.has_permission(self.mock_request, self.mock_view)

        self.assertFalse(result)

    def test_allowed_roles_granted(self) -> None:
        allowed_roles = [
            RoleChoices.TA,
            RoleChoices.LC,
            RoleChoices.OM,
            RoleChoices.ST,
            RoleChoices.AD,
        ]

        permission = AnswerAccessPermission()

        for role in allowed_roles:
            with self.subTest(role=role):
                self.mock_request.user = self._user_with_role(role)
                self.assertTrue(permission.has_permission(self.mock_request, self.mock_view))

    def test_invalid_role_denied(self) -> None:
        user = Mock()
        user.is_authenticated = True
        user.role = "INVALID_ROLE"
        self.mock_request.user = user

        permission = AnswerAccessPermission()
        result = permission.has_permission(self.mock_request, self.mock_view)

        self.assertFalse(result)


"""
test_safe_methods_allowed
    안전한 메서드(GET, HEAD, OPTIONS)는 누구나 허용
test_unsafe_methods_owner_only
    수정/삭제는 작성자만 허용
test_unsafe_methods_non_owner_denied
    ✅ 수정/삭제는 작성자가 아니면 거부
est_object_without_author_denied
    author 속성이 없는 객체는 거부
"""


class TestIsOwnerOrReadOnly(SimpleTestCase):
    def setUp(self) -> None:
        self.mock_view = MagicMock()
        self.mock_request = Mock()
        self.mock_request.user = Mock()

    def test_safe_methods_allowed(self) -> None:
        for method in ["GET", "HEAD", "OPTIONS"]:
            with self.subTest(method=method):
                self.mock_request.method = method

                permission = IsOwnerOrReadOnly()
                obj = Mock()
                obj.author = Mock()

                self.assertTrue(permission.has_object_permission(self.mock_request, self.mock_view, obj))

    def test_unsafe_methods_owner_only(self) -> None:
        for method in ["POST", "PUT", "PATCH", "DELETE"]:
            with self.subTest(method=method):
                user = Mock()
                self.mock_request.user = user
                self.mock_request.method = method

                permission = IsOwnerOrReadOnly()
                obj = Mock()
                obj.author = user

                self.assertTrue(permission.has_object_permission(self.mock_request, self.mock_view, obj))

    def test_unsafe_methods_non_owner_denied(self) -> None:
        for method in ["POST", "PUT", "PATCH", "DELETE"]:
            with self.subTest(method=method):
                self.mock_request.user = Mock()
                self.mock_request.method = method

                permission = IsOwnerOrReadOnly()
                obj = Mock()
                obj.author = Mock()

                self.assertFalse(permission.has_object_permission(self.mock_request, self.mock_view, obj))

    def test_object_without_author_denied(self) -> None:
        self.mock_request.method = "PUT"

        permission = IsOwnerOrReadOnly()
        obj = Mock(spec=[])

        self.assertFalse(permission.has_object_permission(self.mock_request, self.mock_view, obj))


"""
test_question_author_allowed
    질문 작성자는 답변 채택 가능
test_non_question_author_denied
    질문 작성자가 아니면 채택 불가
test_object_without_question_denied
    question 속성이 없는 객체는 거부
"""


class TestIsQuestionAuthor(SimpleTestCase):
    def setUp(self) -> None:
        self.mock_view = MagicMock()
        self.mock_request = Mock()
        self.mock_request.method = "POST"

    def test_question_author_allowed(self) -> None:
        user = Mock()
        self.mock_request.user = user

        question = Mock()
        question.author = user

        answer = Mock()
        answer.question = question

        permission = IsQuestionAuthor()
        result = permission.has_object_permission(self.mock_request, self.mock_view, answer)

        self.assertTrue(result)

    def test_non_question_author_denied(self) -> None:
        self.mock_request.user = Mock()

        question = Mock()
        question.author = Mock()

        answer = Mock()
        answer.question = question

        permission = IsQuestionAuthor()
        result = permission.has_object_permission(self.mock_request, self.mock_view, answer)

        self.assertFalse(result)

    def test_object_without_question_denied(self) -> None:
        obj = Mock(spec=[])

        permission = IsQuestionAuthor()
        result = permission.has_object_permission(self.mock_request, self.mock_view, obj)

        self.assertFalse(result)
