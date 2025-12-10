from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework import status

from apps.user.serializers.verification_serializers import (
    EmailSerializer,
    EmailCodeVerifySerializer,
    FindPasswordSerialzier
)

from apps.user.utils.verification import (
    generate_code,
    verify,
    generate_token
)

from apps.user.utils.email_sender import send_verification_email
from django.contrib.auth import get_user_model

User = get_user_model()


class SignupSendEmailAPIView(APIView):
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        code = generate_code(email)
        send_verification_email(email, code, "회원가입")
        return Response(
            {"detail":"회원가입을 위한 인증코드가 전송되었습니다."},
            status=status.HTTP_200_OK
        )


class SignupVerifyEmailAPIView(APIView):
    def post(self, request):
        serialzier = EmailCodeVerifySerializer(data=request.data)
        serialzier.is_valid(raise_exception=True)
        
        email = serialzier.validated_data["email"]
        code = serialzier.validated_data["code"]

        if not verify(email, code):
            return Response({"detail": "잘못된 인증코드입니다."}, status=400)
        try:
            token = generate_token(email)
        
        except RuntimeError:
            return Response({"detail": "토큰 생성에 실패했습니다."}, status=500)

        return Response(
            {"detail": "회원가입을 위한 이메일 인증에 성공하였습니다.",
             "token": token},
            status=status.HTTP_200_OK
        )


class FindPasswordSendEmailAPIView(APIView):
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        code = generate_code(email)
        send_verification_email(email, code, "비밀번호 찾기")

        return Response(
            {"detail": "비밀번호 찾기를 위한 이메일 인증 코드가 전송되었습니다."},
            status=200
        )


class FindPasswordAPIView(APIView):
    def post(self, reqeust):
        serializer = FindPasswordSerialzier(data=reqeust.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        old_pw = serializer.validated_data["old_password"]
        new_pw = serializer.validated_data["new_password"]
        code = serializer.validated_data["code"]

        if not verify(email, code):
            return Response({"detail": "잘못된 인증코드입니다."}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "존재하지 않는 계정입니다."}, status=404)

        if not user.check_password(old_pw):
            return Response({"detail": "기존 비밀번호가 일치하지 않습니다."}, status=400)

        user.set_password(new_pw)
        user.save()

        return Response({"detail": "비밀번호 변경 성공."}, status=200)


class RestoreSendEmailAPIView(APIView):
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = generate_code(email)

        send_verification_email(email, code, "계정 복구")

        return Response(
            {"detail": "계정복구를 위한 이메일 인증 코드가 전송되었습니다."},
            status=200
        )


class RestoreAPIView(APIView):
    def post(self, request):
        serializer = EmailCodeVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        if not verify(email, code):
            return Response({"detail": "잘못된 인증코드입니다."}, status=400)

        return Response({"detail": "계정복구가 완료되었습니다."}, status=200)