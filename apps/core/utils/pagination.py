from typing import Any

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class Pagination(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "size"
    page_size = 10

    def get_paginated_response(self, data: Any) -> Response:

        return Response(
            {
                "page": self.page.number if self.page else 1,
                "size": self.get_page_size(self.request) or self.page_size,
                "total_count": self.page.paginator.count if self.page else 0,
                "results": data,
            }
        )
