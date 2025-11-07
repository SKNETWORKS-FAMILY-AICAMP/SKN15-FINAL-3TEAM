"""
논문 데이터 Admin 설정
"""
from django.contrib import admin
from django.utils import timezone
from .models import Paper


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    """논문 관리자 페이지"""

    list_display = [
        'id',
        'title_kr_short',
        'authors_short',
        'published_date',
        'created_at_kst',
        'updated_at_kst',
    ]
    list_filter = ['published_date', 'created_at', 'updated_at']
    search_fields = ['title_kr', 'title_en', 'authors', 'abstract_kr', 'abstract_en']
    ordering = ['-created_at']
    list_per_page = 50
    readonly_fields = ['id', 'created_at_kst', 'updated_at_kst']

    def title_kr_short(self, obj):
        """제목 50자까지만 표시"""
        return obj.title_kr[:50] + '...' if len(obj.title_kr) > 50 else obj.title_kr
    title_kr_short.short_description = '논문 제목'

    def authors_short(self, obj):
        """저자 30자까지만 표시"""
        if obj.authors:
            return obj.authors[:30] + '...' if len(obj.authors) > 30 else obj.authors
        return '-'
    authors_short.short_description = '저자'

    def created_at_kst(self, obj):
        """한국 시간으로 생성일 표시"""
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    created_at_kst.short_description = '작성일시 (KST)'
    created_at_kst.admin_order_field = 'created_at'

    def updated_at_kst(self, obj):
        """한국 시간으로 수정일 표시"""
        if obj.updated_at:
            local_time = timezone.localtime(obj.updated_at)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    updated_at_kst.short_description = '수정일시 (KST)'
    updated_at_kst.admin_order_field = 'updated_at'

    fieldsets = (
        ('기본 정보', {
            'fields': ('title_kr', 'title_en', 'authors')
        }),
        ('초록', {
            'fields': ('abstract_kr', 'abstract_en'),
            'classes': ('collapse',)
        }),
        ('링크', {
            'fields': ('pdf_link', 'abstract_page_link', 'source_file')
        }),
        ('날짜 정보', {
            'fields': ('published_date', 'created_at_kst', 'updated_at_kst')
        }),
    )
