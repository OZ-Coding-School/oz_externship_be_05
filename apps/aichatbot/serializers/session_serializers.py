from rest_framework import serializers

from apps.aichatbot.models.chatbot_sessions import ChatbotSession, ChatModel

"""
세션용 serializers
- POST: 세션 생성
- GET: 세션 목록
- DELETE: (명세서 추가해야함) 

Request Body Schema
- POST
"{
  ""question_id"": str | null,
}"

Success Response Schema
- POST
"{
  ""id"": int,
  ""user"": int,
  ""question"": int,
  ""title"": str,
  ""using_model"": str,
  ""created_at"": datetime,
  ""updated_at"": datetime
}"

- GET
"200: {
  ""next"": str | null,
  ""previous"": str | null,
  ""result"": [
    {  
      ""id"": int,
      ""title"": str,
    }
  ]
}"

Error Response Schema
- POST
"400: {
    ""error_detail"": str
}
401: {
    ""error_detail"": str
}
403: {
    ""error_detail"": str
}
404: {
    ""error_detail"": str
}"

- GET
"400: {
    ""error_detail"": str
}
401: {
    ""error_detail"": str
}
403: {
    ""error_detail"": str
}"
"""


# Session의 응답포멧
# source의 mock 날릴것
class SessionSerializer(serializers.ModelSerializer[ChatbotSession]):
    class Meta:
        model = ChatbotSession
        fields = ["id", "user", "question", "title", "using_model", "created_at", "updated_at"]
        read_only_fields = fields


# 세션 생성 요청(question_id 받기)
# 한 시리얼라이저로 요청이랑 응답 스키마를 만들 수 있다. write_only랑 read_only 속성을 잘 사용
class SessionCreateSerializer(serializers.ModelSerializer[ChatbotSession]):
    class Meta:
        model = ChatbotSession
        fields = ["id", "user", "question", "title", "using_model", "created_at", "updated_at"]
        extra_kwargs = {
            "id": {"read_only": True},
            "user": {"read_only": True},
            "using_model": {"read_only": True},
            "title": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
        }
