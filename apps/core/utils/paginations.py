from typing import Any, cast

from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response


class Pagination(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "size"
    page_size = 10

    def get_paginated_response(self, data: Any) -> Response:

        current_size = self.get_page_size(cast(Request, self.request)) or self.page_size

        return Response(
            {
                "page": self.page.number if self.page else 1,
                "size": current_size,
                "count": self.page.paginator.count if self.page else 0,
                "previous": self.get_previous_link(),
                "next": self.get_next_link(),
                "results": data,
            }
        )
