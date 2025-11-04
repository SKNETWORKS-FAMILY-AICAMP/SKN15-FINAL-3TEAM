"""
논문 데이터 모델
"""
from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex


class Paper(models.Model):
    """논문 정보 모델"""

    # 제목
    title_en = models.TextField(
        verbose_name='제목(영문)',
        blank=True,
        null=True
    )
    title_kr = models.TextField(
        verbose_name='제목(한글)',
        db_index=True
    )

    # 저자
    authors = models.TextField(
        verbose_name='저자',
        blank=True,
        null=True
    )

    # 초록
    abstract_en = models.TextField(
        verbose_name='초록(영문)',
        blank=True,
        null=True
    )
    abstract_kr = models.TextField(
        verbose_name='초록(한글)',
        blank=True,
        null=True
    )

    # 링크
    abstract_page_link = models.URLField(
        max_length=500,
        verbose_name='논문 페이지 링크',
        blank=True,
        null=True
    )
    pdf_link = models.URLField(
        max_length=500,
        verbose_name='PDF 링크',
        blank=True,
        null=True
    )

    # 출처 파일
    source_file = models.CharField(
        max_length=255,
        verbose_name='출처 파일',
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
        db_table = 'papers'
        verbose_name = '논문'
        verbose_name_plural = '논문 목록'
        ordering = ['-created_at']
        indexes = [
            # GIN 인덱스 (Full-Text Search용)
            GinIndex(fields=['search_vector']),
        ]

    def __str__(self):
        return f"{self.title_kr[:50]}"
