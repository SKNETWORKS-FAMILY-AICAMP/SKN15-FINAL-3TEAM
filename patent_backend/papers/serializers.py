"""
논문 데이터 Serializer
"""
from rest_framework import serializers
from .models import Paper


class PaperSerializer(serializers.ModelSerializer):
    """논문 전체 정보 Serializer"""

    class Meta:
        model = Paper
        fields = [
            'id',
            'title_en',
            'title_kr',
            'authors',
            'abstract_en',
            'abstract_kr',
            'abstract_page_link',
            'pdf_link',
            'source_file',
            'published_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PaperListSerializer(serializers.ModelSerializer):
    """논문 목록용 간단한 Serializer (검색 결과용)"""

    class Meta:
        model = Paper
        fields = [
            'id',
            'title_kr',
            'authors',
            'abstract_kr',
            'pdf_link',
            'published_date',
        ]


class PaperSearchSerializer(serializers.Serializer):
    """검색 요청 Serializer"""

    keyword = serializers.CharField(
        required=True,
        max_length=200,
        help_text='검색 키워드'
    )
    search_fields = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=['title_kr', 'abstract_kr'],
        help_text='검색 대상 필드: title_kr, title_en, abstract_kr, abstract_en, authors'
    )
    page = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1,
        help_text='페이지 번호'
    )
    page_size = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=100,
        help_text='페이지당 결과 수 (최대 100)'
    )
    sort_by = serializers.CharField(
        required=False,
        allow_blank=True,
        default='date_desc',
        help_text='정렬 방식 (date_desc: 최신순, date_asc: 오래된순, relevance: 관련도순)'
    )
