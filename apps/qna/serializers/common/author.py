from rest_framework import serializers


class AuthorSerializer(serializers.Serializer[dict[str, object]]):
    nickname = serializers.CharField()
    profile_image_url = serializers.CharField(allow_null=True)