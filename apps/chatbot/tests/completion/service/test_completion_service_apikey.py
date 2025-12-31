import os
import unittest
from unittest.mock import patch

from apps.chatbot.services.completion_response_service import GeminiStreamingService

"""
GeminiStreamingService._get_api_key 함수 테스트
API KEY 설정되어 있으면 정상 반환
API KEY 설정X → RuntimeError 발생
API KEY 빈 문자열 → RuntimeError 발생
"""


class TestGetApiKey(unittest.TestCase):
    def test_get_api_key_success(self) -> None:
        env = os.environ.copy()
        env["GEMINI_API_KEY"] = "test-api-key-123"

        patcher = patch.dict("os.environ", env, clear=True)
        patcher.start()
        try:
            result = GeminiStreamingService._get_api_key()
            self.assertEqual(result, "test-api-key-123")
        finally:
            patcher.stop()

    def test_get_api_key_not_set(self) -> None:
        env = os.environ.copy()
        env.pop("GEMINI_API_KEY", None)

        patcher = patch.dict(os.environ, env, clear=True)
        patcher.start()
        try:
            with self.assertRaisesRegex(RuntimeError, r"GEMINI_API_KEY not set"):
                GeminiStreamingService._get_api_key()
        finally:
            patcher.stop()

    def test_get_api_key_empty_string(self) -> None:
        env = os.environ.copy()
        env["GEMINI_API_KEY"] = ""

        patcher = patch.dict(os.environ, env, clear=True)
        patcher.start()
        try:
            with self.assertRaisesRegex(RuntimeError, r"GEMINI_API_KEY not set"):
                GeminiStreamingService._get_api_key()
        finally:
            patcher.stop()
