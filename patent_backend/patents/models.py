"""
특허 데이터 모델
키워드 검색에 최적화된 구조
"""
from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex


class Patent(models.Model):
    """특허 정보 모델"""
    
    # 기본 정보
    title = models.CharField(
        max_length=500,
        verbose_name='발명의명칭',
        db_index=True
    )
    title_en = models.CharField(
        max_length=500,
        verbose_name='발명의명칭(영문)',
        blank=True,
        null=True
    )
    
    # 출원 정보
    application_number = models.CharField(
        max_length=50,
        verbose_name='출원번호',
        unique=True,
        db_index=True
    )
    application_date = models.CharField(
        max_length=20,
        verbose_name='출원일자',
        blank=True,
        null=True
    )
    applicant = models.TextField(
        verbose_name='출원인',
        blank=True,
        null=True
    )
    
    # 등록 정보
    registration_number = models.CharField(
        max_length=50,
        verbose_name='등록번호',
        blank=True,
        null=True,
        db_index=True
    )
    registration_date = models.CharField(
        max_length=20,
        verbose_name='등록일자',
        blank=True,
        null=True
    )
    
    # 분류
    ipc_code = models.TextField(
        verbose_name='IPC분류',
        blank=True,
        null=True
    )
    cpc_code = models.TextField(
        verbose_name='CPC분류',
        blank=True,
        null=True
    )
    
    # 검색 대상 텍스트 (중요!)
    abstract = models.TextField(
        verbose_name='요약',
        blank=True,
        null=True
    )
    claims = models.TextField(
        verbose_name='청구항',
        blank=True,
        null=True
    )
    
    # Full-Text Search Vector (PostgreSQL 전용)
    search_vector = SearchVectorField(
        null=True,
        blank=True
    )
    
    # 메타데이터
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='데이터 생성일'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='데이터 수정일'
    )
    
    class Meta:
        db_table = 'patents'
        verbose_name = '특허'
        verbose_name_plural = '특허 목록'
        ordering = ['-application_date']
        indexes = [
            # GIN 인덱스 (Full-Text Search용)
            GinIndex(fields=['search_vector']),
            # B-tree 인덱스
            models.Index(fields=['application_date']),
            models.Index(fields=['registration_date']),
        ]
    
    def __str__(self):
        return f"{self.application_number} - {self.title[:50]}"
    
    def save(self, *args, **kwargs):
        """저장 시 search_vector 자동 업데이트"""
        super().save(*args, **kwargs)


class RejectDocument(models.Model):
    """특허 거절 사유 문서 모델"""

    doc_id = models.CharField(
        max_length=100,
        verbose_name='문서ID',
        unique=True,
        db_index=True
    )
    send_number = models.CharField(
        max_length=100,
        verbose_name='발송번호',
        blank=True,
        null=True
    )
    send_date = models.CharField(
        max_length=20,
        verbose_name='발송일자',
        blank=True,
        null=True
    )
    applicant_code = models.CharField(
        max_length=50,
        verbose_name='출원인코드',
        blank=True,
        null=True
    )
    applicant = models.TextField(
        verbose_name='출원인',
        blank=True,
        null=True
    )
    agent = models.TextField(
        verbose_name='대리인',
        blank=True,
        null=True
    )
    application_number = models.CharField(
        max_length=50,
        verbose_name='출원번호',
        db_index=True
    )
    invention_name = models.TextField(
        verbose_name='발명의_명칭',
        blank=True,
        null=True
    )
    examination_office = models.TextField(
        verbose_name='심사기관',
        blank=True,
        null=True
    )
    examiner = models.CharField(
        max_length=100,
        verbose_name='심사관',
        blank=True,
        null=True
    )
    tables_raw = models.TextField(
        verbose_name='표_원본',
        blank=True,
        null=True
    )
    processed_text = models.TextField(
        verbose_name='거절사유_내용',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='데이터 생성일'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='데이터 수정일'
    )

    class Meta:
        db_table = 'reject_documents'
        verbose_name = '거절 사유 문서'
        verbose_name_plural = '거절 사유 문서 목록'
        ordering = ['-send_date']
        indexes = [
            models.Index(fields=['application_number']),
            models.Index(fields=['send_date']),
        ]

    def __str__(self):
        return f"{self.application_number} - {self.invention_name[:50] if self.invention_name else 'N/A'}"
