from rest_framework import serializers
from django.conf import settings
from django.contrib.auth.password_validation import validate_password as dj_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.user.utils.validate_token import is_valid_token_format

# 작성하다보니 너무 슈퍼클래스 되고있는거 같기도 하고... 그래도 시리얼라이저 찍어내기 편해서 좋은듯
# 검색 편하게 주석 달아둠 예) [검색어]
# 감사인사는 접어두도록

class BaseMixin:
    
    # [이메일] [email]
    @staticmethod 
    def get_email(**kwargs):
        defaults = dict(required=True)
        defaults.update(kwargs)
        return serializers.EmailField(**defaults)
    
    # [인증코드] [verify_code] [code]
    @staticmethod 
    def get_verify_code(**kwargs):
        """[☠️] validate가 있습니다 !"""
        defaults = dict(
            min_length=getattr(settings, "VERIFYCATION_CODE_LENGTH", 6),
            max_length=getattr(settings, "VERIFYCATION_CODE_LENGTH", 6),
            allow_blank=False,
            required=True
        )
        defaults.update(kwargs)
        return serializers.CharField(**defaults)
    
    def validate_verify_code(self, value: str) -> str:
        if len(value) != getattr(settings,"VERIFYCATION_CODE_LENGTH", 6):
            raise serializers.ValidationError("코드 길이가 올바르지 않습니다.")
        if any(ch not in settings.VERIFYCATION_CODE_CHARS for ch in value):
            raise serializers.ValidationError("코드 형식이 올바르지 않습니다.")
        return value
    
    # [인증 서비스 토큰] [토큰] [verify_token] [token] 
    @staticmethod
    def get_verify_token(**kwargs):
        """[☠️] validate가 있습니다 !"""
        defaults = dict(required=True)
        defaults.update(kwargs)
        return serializers.CharField(**defaults)
    
    def validate_verify_token(self, value: str) -> str:
        if not is_valid_token_format(value, token_bytes=settings.VERIFYCATION_TOKEN_BYTES):
            raise serializers.ValidationError("토큰 형식이 올바르지 않습니다.")
        return value
    
    # [비밀번호] [password] [pw]
    @staticmethod
    def get_password(**kwargs):
        """[☠️] validate가 있습니다 !"""
        defaults = dict(required=True)
        defaults.update(kwargs)
        return serializers.CharField(**defaults)
    
    def validate_password(self, value: str) -> str:
        try:
            dj_validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    # [전화번호] [phone] [phone_number]
    @staticmethod
    def get_phone_number(**kwargs):
        """[☠️] validate가 있습니다 !"""
        defaults = dict(
            max_length=15,
            min_length=9,
            allow_blank=False,
            trim_whitespace=True,
            required=True
        )
        defaults.update(kwargs)
        return serializers.CharField(**defaults)

    def validate_phone_number(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError("전화번호는 숫자만 입력해주세요.")
        return value

