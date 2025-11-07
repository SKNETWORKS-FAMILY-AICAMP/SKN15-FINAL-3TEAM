"""
논문 검색 API Views
OpenSearch 사용
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Q
from .models import Paper
from .serializers import (
    PaperSerializer,
    PaperListSerializer,
    PaperSearchSerializer
)
from patents.opensearch_service import OpenSearchService
import logging

logger = logging.getLogger(__name__)


class PaperViewSet(viewsets.ReadOnlyModelViewSet):
    """
    논문 검색 API

    - 키워드 검색 (PostgreSQL Full-Text Search)
    - 제목, 초록, 저자 검색
    """
    queryset = Paper.objects.all()
    serializer_class = PaperSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        """액션에 따라 다른 Serializer 사용"""
        if self.action == 'list' or self.action == 'search':
            return PaperListSerializer
        return PaperSerializer

    @action(detail=False, methods=['get', 'post'], url_path='search')
    def search(self, request):
        """
        논문 키워드 검색

        GET /api/papers/search/?keyword=인공지능
        POST /api/papers/search/ {"keyword": "인공지능"}
        """
        # 요청 데이터 검증
        if request.method == 'GET':
            serializer = PaperSearchSerializer(data=request.query_params)
        else:
            serializer = PaperSearchSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        keyword = serializer.validated_data['keyword']
        search_fields = serializer.validated_data.get('search_fields', ['title_kr', 'abstract_kr'])
        page = serializer.validated_data.get('page', 1)
        page_size = serializer.validated_data.get('page_size', 10)
        sort_by = serializer.validated_data.get('sort_by', 'date_desc')

        try:
            # OpenSearch 검색
            opensearch_service = OpenSearchService()
            search_results = opensearch_service.search_papers(
                keyword=keyword,
                search_fields=search_fields,
                page=page,
                page_size=page_size,
                sort_by=sort_by
            )

            return Response({
                'success': True,
                'keyword': keyword,
                'total_count': search_results['total_count'],
                'page': search_results['current_page'],
                'page_size': search_results['page_size'],
                'total_pages': search_results['total_pages'],
                'results': search_results['results']
            })

        except Exception as e:
            logger.error(f"논문 검색 오류: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': '검색 중 오류가 발생했습니다.',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='simple-search')
    def simple_search(self, request):
        """
        간단한 키워드 검색 (LIKE 사용 - Full-Text Search가 안 되는 경우 대체)

        GET /api/papers/simple-search/?keyword=인공지능
        """
        keyword = request.query_params.get('keyword', '')

        if not keyword:
            return Response(
                {'error': 'keyword 파라미터가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # LIKE 검색 (간단하지만 느림)
        results = Paper.objects.filter(
            Q(title_kr__icontains=keyword) |
            Q(title_en__icontains=keyword) |
            Q(abstract_kr__icontains=keyword) |
            Q(authors__icontains=keyword)
        ).order_by('-created_at')[:50]  # 최대 50건

        serializer = PaperListSerializer(results, many=True)

        return Response({
            'success': True,
            'keyword': keyword,
            'count': results.count(),
            'results': serializer.data
        })
