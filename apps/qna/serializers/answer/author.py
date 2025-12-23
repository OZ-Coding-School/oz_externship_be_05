from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class AnswerAuthorSerializer(serializers.ModelSerializer[Any]):
    class Meta:
        model = User
        fields = ["id", "nickname", "profile_image_url", "role"]
        read_only_fields = fields
