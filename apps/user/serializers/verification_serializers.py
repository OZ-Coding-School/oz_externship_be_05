from rest_framework import serializers

class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class EmailCodeVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=5)

class FindPasswordSerialzier(serializers.Serializer):
    email = serializers.EmailField()
    old_password = serializers.CharField()
    new_password = serializers.CharField()
    new_password = serializers.CharField()
    code = serializers.CharField(max_length=6)
    