"""
특허 검색 API Views
PostgreSQL Full-Text Search 사용
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Q, F
from .models import Patent, RejectDocument, OpinionDocument
from .serializers import (
    PatentSerializer,
    PatentListSerializer,
    PatentSearchSerializer,
    RejectDocumentSerializer,
    OpinionDocumentSerializer
)
import logging

logger = logging.getLogger(__name__)


class PatentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    특허 검색 API
    
    - 키워드 검색 (PostgreSQL Full-Text Search)
    - 필터링 (출원일, 등록번호 등)
    """
    queryset = Patent.objects.all()
    serializer_class = PatentSerializer
    permission_classes = [AllowAny]  # TODO: 테스트용, 나중에 IsAuthenticated로 변경
    
    def get_serializer_class(self):
        """액션에 따라 다른 Serializer 사용"""
        if self.action == 'list' or self.action == 'search':
            return PatentListSerializer
        return PatentSerializer
    
    @action(detail=False, methods=['get', 'post'], url_path='search')
    def search(self, request):
        """
        특허 키워드 검색
        
        GET /api/patents/search/?keyword=인공지능
        POST /api/patents/search/ {"keyword": "인공지능"}
        """
        # 요청 데이터 검증
        if request.method == 'GET':
            serializer = PatentSearchSerializer(data=request.query_params)
        else:
            serializer = PatentSearchSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        keyword = serializer.validated_data['keyword']
        search_fields = serializer.validated_data.get('search_fields', ['title', 'abstract', 'claims'])
        page = serializer.validated_data.get('page', 1)
        page_size = serializer.validated_data.get('page_size', 10)
        ipc_code = serializer.validated_data.get('ipc_code', '')
        application_start_date = serializer.validated_data.get('application_start_date', '')
        application_end_date = serializer.validated_data.get('application_end_date', '')
        registration_start_date = serializer.validated_data.get('registration_start_date', '')
        registration_end_date = serializer.validated_data.get('registration_end_date', '')
        legal_status = serializer.validated_data.get('legal_status', '')

        try:
            # 키워드가 비어있는 경우 (필터만 사용)
            if not keyword or keyword.strip() == '':
                # 필터만 적용하여 전체 데이터 조회
                results = Patent.objects.all()
            else:
                # PostgreSQL Full-Text Search
                query = SearchQuery(keyword, config='simple')  # 한글은 'simple' 사용

                # 검색 벡터 생성 (동적으로 필드 선택)
                search_vector = None
                if 'title' in search_fields:
                    search_vector = SearchVector('title', weight='A')
                if 'abstract' in search_fields:
                    if search_vector:
                        search_vector += SearchVector('abstract', weight='B')
                    else:
                        search_vector = SearchVector('abstract', weight='B')
                if 'claims' in search_fields:
                    if search_vector:
                        search_vector += SearchVector('claims', weight='C')
                    else:
                        search_vector = SearchVector('claims', weight='C')

                # 검색 필드가 하나도 선택되지 않은 경우 기본값 사용
                if not search_vector:
                    search_vector = SearchVector('title', weight='A')

                # 검색 실행 및 랭킹
                results = Patent.objects.annotate(
                    rank=SearchRank(search_vector, query)
                ).filter(
                    rank__gte=0.001  # 최소 관련도 필터
                )

            # 고급 필터 적용
            if ipc_code:
                results = results.filter(
                    Q(ipc_code__icontains=ipc_code) | Q(cpc_code__icontains=ipc_code)
                )

            if application_start_date:
                # 날짜 형식 정규화 (YYYY-MM-DD -> YYYYMMDD)
                app_start = application_start_date.replace('-', '')
                results = results.filter(application_date__gte=app_start)

            if application_end_date:
                app_end = application_end_date.replace('-', '')
                results = results.filter(application_date__lte=app_end)

            if registration_start_date:
                reg_start = registration_start_date.replace('-', '')
                results = results.filter(registration_date__gte=reg_start)

            if registration_end_date:
                reg_end = registration_end_date.replace('-', '')
                results = results.filter(registration_date__lte=reg_end)

            if legal_status:
                results = results.filter(legal_status__icontains=legal_status)

            # 정렬 (키워드가 있으면 랭킹순, 없으면 출원일순)
            if keyword and keyword.strip():
                results = results.order_by('-rank', '-application_date')
            else:
                results = results.order_by('-application_date')
            
            # 페이지네이션
            total_count = results.count()
            start = (page - 1) * page_size
            end = start + page_size
            paginated_results = results[start:end]
            
            # 응답 데이터 구성
            result_serializer = PatentListSerializer(paginated_results, many=True)
            
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
            logger.error(f"특허 검색 오류: {str(e)}")
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
        
        GET /api/patents/simple-search/?keyword=인공지능
        """
        keyword = request.query_params.get('keyword', '')
        
        if not keyword:
            return Response(
                {'error': 'keyword 파라미터가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # LIKE 검색 (간단하지만 느림)
        results = Patent.objects.filter(
            Q(title__icontains=keyword) |
            Q(abstract__icontains=keyword) |
            Q(claims__icontains=keyword)
        ).order_by('-application_date')[:50]  # 최대 50건
        
        serializer = PatentListSerializer(results, many=True)

        return Response({
            'success': True,
            'keyword': keyword,
            'count': results.count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='reject-reasons/(?P<application_number>[^/.]+)')
    def reject_reasons(self, request, application_number=None):
        """
        특허 출원번호로 거절 사유 조회

        GET /api/patents/reject-reasons/1020190012345/
        """
        if not application_number:
            return Response(
                {'error': '출원번호가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 출원번호로 거절 사유 문서 조회
            reject_docs = RejectDocument.objects.filter(
                application_number=application_number
            ).order_by('-send_date')

            if not reject_docs.exists():
                return Response({
                    'success': True,
                    'application_number': application_number,
                    'has_reject_reasons': False,
                    'count': 0,
                    'results': []
                })

            serializer = RejectDocumentSerializer(reject_docs, many=True)

            return Response({
                'success': True,
                'application_number': application_number,
                'has_reject_reasons': True,
                'count': reject_docs.count(),
                'results': serializer.data
            })

        except Exception as e:
            logger.error(f"거절 사유 조회 오류: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': '거절 사유 조회 중 오류가 발생했습니다.',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='opinion-documents/(?P<application_number>[^/.]+)')
    def opinion_documents(self, request, application_number=None):
        """
        특허 출원번호로 의견 제출 통지서 조회

        GET /api/patents/opinion-documents/1020190012345/
        """
        if not application_number:
            return Response(
                {'error': '출원번호가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 출원번호로 의견 제출 통지서 조회
            opinion_docs = OpinionDocument.objects.filter(
                application_number=application_number
            ).order_by('-created_at')

            if not opinion_docs.exists():
                return Response({
                    'success': True,
                    'application_number': application_number,
                    'has_opinion_documents': False,
                    'count': 0,
                    'results': []
                })

            serializer = OpinionDocumentSerializer(opinion_docs, many=True)

            return Response({
                'success': True,
                'application_number': application_number,
                'has_opinion_documents': True,
                'count': opinion_docs.count(),
                'results': serializer.data
            })

        except Exception as e:
            logger.error(f"의견 제출 통지서 조회 오류: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': '의견 제출 통지서 조회 중 오류가 발생했습니다.',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
