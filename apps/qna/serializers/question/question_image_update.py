from rest_framework import serializers

class QuestionImagePatchSerializer(serializers.Serializer):
    delete_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
    )
    add_urls = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        default=list,
    )
