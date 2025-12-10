from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import AllowAny
from apps.user.serializers.sms_serializer import SMSRequestSerializer, SMSVerifySerializer
from apps.user.utils.verification import generate_code, verify, generate_token
from apps.user.utils.sms_sender import send_verification_code, check_verification_code
from apps.user.utils.email_masker import mask_email
from django.contrib.auth import get_user_model

from rest_framework.views import APIView

User = get_user_model()

from twilio.base.exceptions import TwilioRestException

class SendSmsCode(APIView):

    permission_classes = [AllowAny]

    def post(self,request):
        serializer = SMSRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]

        try:
            send_verification_code(phone)
        except:
            Response({"detail": "인증 코드 발송에 실패했습니다."}, status=500)

        return Response({"detail": "인증 코드가 발송되었습니다."}, status=200)

class VerifySmsCode(APIView):

    permission_classes = [AllowAny]

    def post(self,request):
        serializer = SMSVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]

        if check_verification_code(phone, code):
            return Response({"detail": "SMS 인증이 완료되었습니다."}, status=200)
        return Response({"detail": "SMS 인증코드가 잘못되었습니다."}, status=400)

class VerifySMSCodeToken(APIView):

    permission_classes = [AllowAny]

    def post(self,request):
        serializer = SMSVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]
        token = generate_token(phone)

        if check_verification_code(phone, code):
            return Response({"detail": "SMS 인증이 완료되었습니다.", "token" : token}, status=200)
        return Response({"error_detail": "SMS 인증코드가 잘못되었습니다."}, status=400)
    
class FindEmailViaSMS(APIView):

    permission_classes = [AllowAny]

    def post(self,request):
        serializer = SMSVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]
        if check_verification_code(phone, code):
            try:
                user: User = User.objects.get(phone_number=phone)
                email = mask_email(user.get_username())
            except User.DoesNotExist:
                return Response({"error_detail": "해당하는 유저를 찾을 수 없습니다."}, status=403)
            return Response({"email": email}, status=200)