from typing import Any, Optional

from django.test import TestCase

from apps.chatbot.serializers.completion_serializers import CompletionCreateSerializer


class CompletionCreateSerializerTests(TestCase):
    # 공통 검증용 헬퍼 (유효 시 true, 무효 시 false 선언)
    def _check_payload(
        self,
        data: dict[str, Any],
        expect_valid: bool,
        field: str = "message",
    ) -> CompletionCreateSerializer:

        serializer = CompletionCreateSerializer(data=data)
        is_valid = serializer.is_valid()
        # 유효 케이스
        if expect_valid:
            self.assertEqual(is_valid, serializer.errors)
        # 유효하지 않은 케이스
        else:
            self.assertFalse(is_valid)
            self.assertIn(field, serializer.errors)
        return serializer

    # 검증이 올바를 때
    def test_valid_payload_create_completion(self) -> None:
        data: dict[str, str] = {"message": "AI에게 질문."}
        serializer = self._check_payload(data, expect_valid=True)
        self.assertEqual(serializer.validated_data["message"], data["message"])

    # 메세지 누락 케이스
    def test_missing_message(self) -> None:
        data: dict[str, str] = {}
        self._check_payload(data, expect_valid=False)

    # 빈 메세지면 invalid 나오나요
    def test_blank_message(self) -> None:
        data: dict[str, str] = {
            "message": "",
        }
        self._check_payload(data, expect_valid=False)
