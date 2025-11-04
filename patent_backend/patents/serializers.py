"""
특허 데이터 Serializer
"""
from rest_framework import serializers
from .models import Patent, RejectDocument, OpinionDocument


class PatentSerializer(serializers.ModelSerializer):
    """특허 전체 정보 Serializer"""

    class Meta:
        model = Patent
        fields = [
            'id',
            'title',
            'title_en',
            'application_number',
            'application_date',
            'applicant',
            'registration_number',
            'registration_date',
            'ipc_code',
            'cpc_code',
            'abstract',
            'claims',
            'legal_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PatentListSerializer(serializers.ModelSerializer):
    """특허 목록용 간단한 Serializer (검색 결과용)"""

    class Meta:
        model = Patent
        fields = [
            'id',
            'title',
            'application_number',
            'application_date',
            'applicant',
            'registration_number',
            'abstract',
            'legal_status',
        ]


class PatentSearchSerializer(serializers.Serializer):
    """검색 요청 Serializer"""

    keyword = serializers.CharField(
        required=True,
        max_length=200,
        help_text='검색 키워드'
    )
    search_fields = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=['title', 'abstract', 'claims'],
        help_text='검색 대상 필드: title, abstract, claims'
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
    # 고급 필터
    ipc_code = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='IPC/CPC 코드 (부분 검색)'
    )
    application_start_date = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='출원일 시작 (YYYY-MM-DD 또는 YYYYMMDD)'
    )
    application_end_date = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='출원일 종료 (YYYY-MM-DD 또는 YYYYMMDD)'
    )
    registration_start_date = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='등록일 시작 (YYYY-MM-DD 또는 YYYYMMDD)'
    )
    registration_end_date = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='등록일 종료 (YYYY-MM-DD 또는 YYYYMMDD)'
    )
    legal_status = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='법적상태 (등록, 공개, 거절, 취하, 포기, 소멸 등)'
    )


class RejectDocumentSerializer(serializers.ModelSerializer):
    """거절 사유 문서 Serializer"""

    class Meta:
        model = RejectDocument
        fields = [
            'id',
            'doc_id',
            'send_number',
            'send_date',
            'applicant_code',
            'applicant',
            'agent',
            'application_number',
            'invention_name',
            'examination_office',
            'examiner',
            'tables_raw',
            'processed_text',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class OpinionDocumentSerializer(serializers.ModelSerializer):
    """의견 제출 통지서 Serializer"""

    class Meta:
        model = OpinionDocument
        fields = [
            'id',
            'application_number',
            'full_text',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
