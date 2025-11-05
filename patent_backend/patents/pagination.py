"""
커스텀 페이지네이션 클래스
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class CustomPageNumberPagination(PageNumberPagination):
    """
    페이지 범위를 자동으로 조정하는 커스텀 페이지네이션
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        """
        페이지 번호가 범위를 벗어나면 자동으로 조정
        """
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)

        try:
            page_number = int(page_number)
        except (TypeError, ValueError):
            page_number = 1

        # 페이지 범위 검증 및 자동 조정
        if page_number < 1:
            page_number = 1
        elif page_number > paginator.num_pages > 0:
            page_number = paginator.num_pages

        try:
            self.page = paginator.page(page_number)
        except Exception:
            # 모든 예외에 대해 첫 페이지로 폴백
            self.page = paginator.page(1)

        if paginator.num_pages > 1 and self.template is not None:
            self.display_page_controls = True

        self.request = request
        return list(self.page)

    def get_paginated_response(self, data):
        """
        커스텀 페이지네이션 응답
        """
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('results', data)
        ]))
