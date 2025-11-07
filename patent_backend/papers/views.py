"""
논문 검색 API Views
PostgreSQL Full-Text Search 사용
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
            # PostgreSQL Full-Text Search
            query = SearchQuery(keyword, config='simple')

            # 검색 벡터 생성 (동적으로 필드 선택)
            search_vector = None
            if 'title_kr' in search_fields:
                search_vector = SearchVector('title_kr', weight='A')
            if 'title_en' in search_fields:
                if search_vector:
                    search_vector += SearchVector('title_en', weight='B')
                else:
                    search_vector = SearchVector('title_en', weight='B')
            if 'abstract_kr' in search_fields:
                if search_vector:
                    search_vector += SearchVector('abstract_kr', weight='B')
                else:
                    search_vector = SearchVector('abstract_kr', weight='B')
            if 'abstract_en' in search_fields:
                if search_vector:
                    search_vector += SearchVector('abstract_en', weight='C')
                else:
                    search_vector = SearchVector('abstract_en', weight='C')
            if 'authors' in search_fields:
                if search_vector:
                    search_vector += SearchVector('authors', weight='C')
                else:
                    search_vector = SearchVector('authors', weight='C')

            # 검색 필드가 하나도 선택되지 않은 경우 기본값 사용
            if not search_vector:
                search_vector = SearchVector('title_kr', weight='A') + SearchVector('abstract_kr', weight='B')

            # 검색 실행 및 랭킹
            results = Paper.objects.annotate(
                rank=SearchRank(search_vector, query)
            ).filter(
                rank__gte=0.001  # 최소 관련도 필터
            )

            # 정렬 순서 설정
            if sort_by == 'date_asc':
                # 오래된 순 (발행일 기준)
                results = results.order_by('published_date', 'created_at')
            elif sort_by == 'relevance':
                # 관련도순 (검색 점수 기준)
                results = results.order_by('-rank', '-published_date')
            else:  # date_desc (기본값)
                # 최신순 (발행일 기준)
                results = results.order_by('-published_date', '-created_at')

            # 페이지네이션
            total_count = results.count()
            start = (page - 1) * page_size
            end = start + page_size
            paginated_results = results[start:end]

            # 응답 데이터 구성
            result_serializer = PaperListSerializer(paginated_results, many=True)

            return Response({
                'success': True,
                'keyword': keyword,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size,
                'results': result_serializer.data
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
