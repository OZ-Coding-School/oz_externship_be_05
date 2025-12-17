from rest_framework import serializers

from apps.chatbot.models.chatbot_completions import ChatbotCompletion

"""
컴플리션용 serializers
- POST: 챗봇 응답 생성
- GET: 챗봇 대화내역 조회
- DELETE: 챗봇 대화내역 초기화

Request Body Schema
- POST
"{
  ""message"": 
    type: str,
    required: True
}"
- GET
- DELETE

Query Parameters
- GET
"{
  ""cursor"": str,
  ""page_size"": int,
}"

Success Response Schema
- POST
"data: {
  ""content"": ""r""
}
data: {
  ""content"": ""e""
}
data: {
  ""content"": ""a""
}
data: {
  ""content"": ""c""
}
data: {
  ""content"": ""t""
}
모든 청크 전송 후:
data: [DONE]"

- GET
"200: {
  ""next"": str | null,
  ""previous"": str | null,
  ""result"": [
    {  
      ""id"": int,
      ""prompt"": str,
      ""output"": str,
      ""created_at"": datetime
    }
  ]
}"

- DELETE
"200: {
  ""detail"": str
}"

Error Response Schema
- POST, GET, DELETE 동일 but 들어가는 메세지 다름
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


# Completion의 응답 포멧
class CompletionSerializer(serializers.ModelSerializer[ChatbotCompletion]):
    class Meta:
        model = ChatbotCompletion
        fields = ["id", "session", "message", "role", "created_at", "updated_at"]
        read_only_fields = fields


# completion 생성 (요청 - Request)
class CompletionCreateSerializer(serializers.ModelSerializer[ChatbotCompletion]):
    message = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = ChatbotCompletion
        fields = ["id", "session", "message", "role", "created_at", "updated_at"]
        extra_kwargs = {
            "id": {"read_only": True},
            "session": {"read_only": True},
            "role": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
        }
