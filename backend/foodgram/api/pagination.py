from rest_framework import pagination


class PageNumberLimitPagination(pagination.PageNumberPagination):
    page_size_query_param = "limit"
