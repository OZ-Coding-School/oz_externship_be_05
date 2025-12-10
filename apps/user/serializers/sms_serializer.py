from rest_framework import serializers


class SMSRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=15,
        min_length=9,
        allow_blank=False,
        trim_whitespace=True,
    )

    def validate_phone_number(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError("전화번호는 숫자만 입력해주세요.")
        return value

class SMSVerifySerializer(SMSRequestSerializer):
    code = serializers.CharField(min_length=6, max_length=6, allow_blank=False)