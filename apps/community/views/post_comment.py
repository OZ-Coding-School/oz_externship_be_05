from rest_framework.views import APIView


class PostCommentListCreateAPIView(APIView):

    def get_post_id(self, request):
        return request.query_params.get("post_id")

    def get(self,request, *args, **kwargs):
        post_id = self.get_post_id(request)
        pass

    def post(self,request, *args, **kwargs):
        post_id = self.get_post_id(request)
        pass

class PostCommentUpdateDestroyAPIView(APIView):

    def get_post_id(self, request):
        return request.query_params.get("post_id")

    def get_comment_id(self, request):
        return request.query_params.get("comment_id")

    def put(self,request, *args, **kwargs):
        post_id = self.get_post_id(request)
        comment_id = self.get_comment_id(request)
        pass

    def delete(self,request, *args, **kwargs):
        post_id = self.get_post_id(request)
        comment_id = self.get_comment_id(request)
        pass

