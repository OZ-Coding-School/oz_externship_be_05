import unittest
from unittest.mock import MagicMock, patch

from apps.chatbot.services.completion_response_service import GeminiStreamingService

"""
GeminiStreamingService._get_client 함수 테스트
API KEY 설정되어 있으면 정상 반환
API KEY 설정X → RuntimeError 발생
"""


class TestGetClient(unittest.TestCase):
    def test_get_client_success(self) -> None:
        mock_client_instance = MagicMock()

        patcher_get_api_key = patch.object(
            GeminiStreamingService,
            "_get_api_key",
            return_value="test-api-key",
        )
        patcher_client_class = patch(
            "apps.chatbot.services.completion_response_service.genai.Client",
            return_value=mock_client_instance,
        )

        mocked_get_api_key = patcher_get_api_key.start()
        mocked_client_class = patcher_client_class.start()
        try:
            result = GeminiStreamingService._get_client()

            mocked_get_api_key.assert_called_once()
            mocked_client_class.assert_called_once_with(api_key="test-api-key")
            self.assertIs(result, mock_client_instance)
        finally:
            patcher_client_class.stop()
            patcher_get_api_key.stop()

    def test_get_client_raises_when_no_api_key(self) -> None:
        patcher_get_api_key = patch.object(
            GeminiStreamingService,
            "_get_api_key",
            side_effect=RuntimeError("GEMINI_API_KEY not set"),
        )

        patcher_get_api_key.start()
        try:
            with self.assertRaisesRegex(RuntimeError, r"GEMINI_API_KEY not set"):
                GeminiStreamingService._get_client()
        finally:
            patcher_get_api_key.stop()
