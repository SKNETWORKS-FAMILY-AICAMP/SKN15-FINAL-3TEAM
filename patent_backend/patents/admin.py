"""
특허 데이터 Admin 설정
"""
from django.contrib import admin
from .models import Patent


@admin.register(Patent)
class PatentAdmin(admin.ModelAdmin):
    """특허 관리자 페이지"""
    
    list_display = [
        'id',
        'title_short',
        'application_number',
        'application_date',
        'applicant_short',
        'registration_number',
    ]
    list_filter = ['application_date', 'registration_date']
    search_fields = ['title', 'application_number', 'applicant', 'abstract']
    ordering = ['-application_date']
    list_per_page = 50
    
    def title_short(self, obj):
        """제목 50자까지만 표시"""
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = '발명의명칭'
    
    def applicant_short(self, obj):
        """출원인 30자까지만 표시"""
        if obj.applicant:
            return obj.applicant[:30] + '...' if len(obj.applicant) > 30 else obj.applicant
        return '-'
    applicant_short.short_description = '출원인'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'title_en')
        }),
        ('출원 정보', {
            'fields': ('application_number', 'application_date', 'applicant')
        }),
        ('등록 정보', {
            'fields': ('registration_number', 'registration_date')
        }),
        ('분류', {
            'fields': ('ipc_code', 'cpc_code'),
            'classes': ('collapse',)
        }),
        ('내용', {
            'fields': ('abstract', 'claims'),
            'classes': ('collapse',)
        }),
    )
