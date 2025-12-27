from __future__ import annotations

from typing import Any

from rest_framework import serializers


class ExamResultQuestionSerializer(serializers.Serializer[Any]):
    """
    결과 화면에서 문제 1개를 표현하는 Serializer
    - DB 모델과 1:1 매핑이 아니라, 결과 응답 JSON 형태를 맞추기 위한 용도
    """

    # 문제 ID
    question_id = serializers.IntegerField()

    # 문제 번호(1, 2, 3 ...)
    number = serializers.IntegerField()

    # 문제 유형
    type = serializers.CharField()

    # 문제 내용
    question = serializers.CharField()
    prompt = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    # 배점
    point = serializers.IntegerField()

    # 선택지 목록
    options = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )

    # 사용자가 제출한 답안
    submitted_answer = serializers.JSONField(
        required=False,
        allow_null=True,
    )

    # 정답
    correct_answer = serializers.JSONField(
        required=False,
        allow_null=True,
    )

    # 정답 여부
    is_correct = serializers.BooleanField()

    # 해설
    explanation = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class ExamResultSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """
    시험 결과 조회 API의 최상위 응답 Serializer
    """

    # 시험 제목
    exam_title = serializers.CharField()

    # 시험 썸네일 이미지 URL
    thumbnail_img_url = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    # 응시 시간("HH:MM:SS")
    duration = serializers.CharField()

    # 획득 점수
    score = serializers.IntegerField()

    # 총점
    total_score = serializers.IntegerField()

    # 부정행위 횟수
    cheating_count = serializers.IntegerField()

    # 문항별 결과 목록
    questions = ExamResultQuestionSerializer(
        many=True,
    )
