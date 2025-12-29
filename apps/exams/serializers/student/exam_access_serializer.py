from typing import Any

from rest_framework import serializers

from apps.core.exceptions.exception_messages import EMS


class ExamAccessCodeSerializer(serializers.Serializer[Any]):
    """
    참가 코드 검증 요청 시리얼라이저
    """

    code = serializers.CharField(
        write_only=True,
        max_length=6,
        error_messages={
            "required": EMS.E400_REQUIRED_FIELD["error_detail"],
            "blank": EMS.E400_REQUIRED_FIELD["error_detail"],
        },
    )

    def validate_code(self, value: str) -> str:
        return value.strip()
