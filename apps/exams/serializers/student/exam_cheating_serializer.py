from typing import Any

from rest_framework import serializers


class ExamCheatingRequestSerializer(serializers.Serializer[Any]):
    """
    부정행위 체크 요청 시리얼라이저
    """

    event = serializers.ChoiceField(choices=["focus_out"])


class ExamCheatingResponseSerializer(serializers.Serializer[Any]):
    """
    부정행위 체크 응답 시리얼라이저
    """

    cheating_count = serializers.IntegerField()
    is_forced_submitted = serializers.BooleanField()
