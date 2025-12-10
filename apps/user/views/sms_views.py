from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from apps.user.serializers.sms_serializer import SMSRequestSerializer, SMSVerifySerializer
from apps.user.utils.verification import generate_code, verify, generate_token
from apps.user.utils.sms_sender import send_verification_code

from twilio.base.exceptions import TwilioRestException

@api_view(["POST"])
def send_sms_code(request):
    serializer = SMSRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    phone = serializer.validated_data["phone_number"]
    code = generate_code(phone)
    try:
        send_verification_code(phone,code)
    except:
        Response({"detail": "인증 코드 발송에 실패했습니다."}, status=500)

    return Response({"detail": "인증 코드가 발송되었습니다."}, status=200)

@api_view(["POST"])
def verify_sms_code(request):
    serializer = SMSVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    phone = serializer.validated_data["phone_number"]
    code = serializer.validated_data["code"]

    if verify(phone, code, consume=False):
        return Response({"detail": "SMS 인증이 완료되었습니다."}, status=200)
    return Response({"detail": "SMS 인증코드가 잘못되었습니다."}, status=400)

@api_view(["POST"])
def verify_sms_code_return_with_token(request):
    serializer = SMSVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    phone = serializer.validated_data["phone_number"]
    code = serializer.validated_data["code"]
    token = generate_token(phone)

    if verify(phone, code, consume=False):
        return Response({"detail": "SMS 인증이 완료되었습니다.", "token" : token}, status=200)
    return Response({"detail": "SMS 인증코드가 잘못되었습니다."}, status=400)