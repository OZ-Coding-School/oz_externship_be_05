from rest_framework import serializers


class NaverProfileSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    email = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    birthyear = serializers.CharField(required=True)
    birthday = serializers.CharField(required=True)


class KakaoProfileSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    kakao_account = serializers.DictField(required=True)

    def validate(self, attrs):
        kakao_account = attrs.get("kakao_account", {})

        profile = kakao_account.get("profile") or {}
        if "nickname" not in profile:
            raise serializers.ValidationError({"nickname": ["이 필드는 필수 항목입니다."]})

        # birthday는 지금은 필수 x
        # if "birthday" not in kakao_account:
        #     raise serializers.ValidationError(
        #         {"birthday": ["이 필드는 필수 항목입니다."]}
        #     )
        
        if "email" not in kakao_account:
            raise serializers.ValidationError({"email": ["이 필드는 필수 항목입니다."]})

        return attrs