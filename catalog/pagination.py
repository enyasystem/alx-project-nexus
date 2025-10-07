from rest_framework.pagination import CursorPagination


class ProductCursorPagination(CursorPagination):
    page_size = 10
    # allow clients to control page size using the `limit` query param (keeps compatibility
    # with previous LimitOffset clients/tests)
    page_size_query_param = 'limit'
    ordering = '-created_at'
\n