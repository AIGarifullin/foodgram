from rest_framework.pagination import PageNumberPagination


class PageNumberPaginator(PageNumberPagination):
    """Пагинатор с лимитом."""

    page_size_query_param = 'limit'
    page_size = 6
