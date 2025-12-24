from rest_framework import serializers

from apps.courses.models import Subject


class SubjectSimpleSerializer(serializers.ModelSerializer[Subject]):
    """
    Subject의 기본 정보(id, title)만 제공하는 재사용 가능 시리얼라이저
    """

    class Meta:
        model = Subject
        fields = ["id", "title"]
        read_only_fields = fields
