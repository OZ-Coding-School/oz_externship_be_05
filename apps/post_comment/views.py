import random
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User, GenderChoices, SocialUser, SocialProvider
from apps.users.serializers import SignUpSerializer, UserInfoSerializer


class PostCommentRetrieveAPIView(APIView):

    def get(self, request: Request, *args, **kwargs):
        pass

class PostCommentCreateAPIView(APIView):

    def post(self, request: Request, *args, **kwargs):
        pass

class PostCommentUpdateDeleteAPIView(APIView):

    def put(self, request: Request, *args, **kwargs):
        pass

    def delete(self, request: Request, *args, **kwargs):
        pass

