"""
특허 검색 API Views
OpenSearch 사용
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from .models import Patent, RejectDocument, OpinionDocument
from .serializers import (
    PatentSerializer,
    PatentListSerializer,
    PatentSearchSerializer,
    RejectDocumentSerializer,
    OpinionDocumentSerializer
)
from .pagination import CustomPageNumberPagination
from .opensearch_service import OpenSearchService
import logging

logger = logging.getLogger(__name__)


class PatentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    특허 검색 API

    - 키워드 검색 (OpenSearch)
    - 필터링 (출원일, IPC/CPC 코드, 법적상태 등)
    """
    queryset = Patent.objects.all()
    serializer_class = PatentSerializer
    permission_classes = [AllowAny]  # TODO: 테스트용, 나중에 IsAuthenticated로 변경
    pagination_class = CustomPageNumberPagination
    
    def get_serializer_class(self):
        """액션에 따라 다른 Serializer 사용"""
        if self.action == 'list' or self.action == 'search':
            return PatentListSerializer
        return PatentSerializer

    def list(self, request, *args, **kwargs):
        """
        전체 특허 목록 조회 (정렬 지원)

        GET /api/patents/?page=1&page_size=10&sort_by=date_desc
        """
        sort_by = request.query_params.get('sort_by', 'date_desc')

        # 정렬 방식에 따라 queryset 정렬
        if sort_by == 'relevance' or sort_by == 'date_desc':
            # 관련도순은 전체 목록에서는 최신순과 동일
            queryset = self.queryset.order_by('-application_date', '-id')
        elif sort_by == 'date_asc':
            # 오래된순
            queryset = self.queryset.order_by('application_date', 'id')
        else:
            # 기본값: 최신순
            queryset = self.queryset.order_by('-application_date', '-id')

        # 페이지네이션 적용
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'post'], url_path='search')
    def search(self, request):
        """
        특허 키워드 검색 (OpenSearch 사용)

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
        sort_by = serializer.validated_data.get('sort_by', 'date_desc')

        try:
            # OpenSearch 서비스 사용
            opensearch_service = OpenSearchService()

            # 필터 구성
            filters = {}
            if ipc_code:
                filters['ipc_code'] = ipc_code
            if application_start_date:
                filters['application_start_date'] = application_start_date.replace('-', '.')
            if application_end_date:
                filters['application_end_date'] = application_end_date.replace('-', '.')
            if registration_start_date:
                filters['registration_start_date'] = registration_start_date.replace('-', '.')
            if registration_end_date:
                filters['registration_end_date'] = registration_end_date.replace('-', '.')
            if legal_status:
                filters['legal_status'] = legal_status

            # OpenSearch 검색 실행
            search_result = opensearch_service.search_patents(
                keyword=keyword if keyword else '',
                search_fields=search_fields,
                filters=filters if filters else None,
                page=page,
                page_size=page_size,
                sort_by=sort_by
            )

            # 응답 데이터 구성
            response_data = {
                'results': search_result['results'],
                'total_count': search_result['total_count'],
                'total_pages': search_result['total_pages'],
                'current_page': search_result['current_page'],
                'page_size': search_result['page_size']
            }

            return Response({
                'success': True,
                'keyword': keyword,
                **response_data
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
        간단한 키워드 검색 (LIKE 사용 - OpenSearch가 안 되는 경우 백업용)

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
