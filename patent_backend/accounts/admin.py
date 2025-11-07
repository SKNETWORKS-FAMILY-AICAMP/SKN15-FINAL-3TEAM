"""
Django Admin 설정
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from .models import Company, Department, User, AdminRequest


# ======================================================
# Company Admin
# ======================================================

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """회사 관리자 페이지"""
    list_display = ['company_id', 'name', 'domain', 'created_at_kst']
    search_fields = ['name', 'domain']
    readonly_fields = ['company_id', 'created_at_kst', 'updated_at_kst']
    ordering = ['name']

    def created_at_kst(self, obj):
        """한국 시간으로 생성일 표시"""
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    created_at_kst.short_description = '생성일시 (KST)'
    created_at_kst.admin_order_field = 'created_at'

    def updated_at_kst(self, obj):
        """한국 시간으로 수정일 표시"""
        if obj.updated_at:
            local_time = timezone.localtime(obj.updated_at)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    updated_at_kst.short_description = '수정일시 (KST)'
    updated_at_kst.admin_order_field = 'updated_at'


# ======================================================
# Department Admin
# ======================================================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """부서 관리자 페이지"""
    list_display = ['department_id', 'company', 'name', 'created_at_kst']
    list_filter = ['company']
    search_fields = ['name', 'company__name']
    readonly_fields = ['department_id', 'created_at_kst', 'updated_at_kst']
    ordering = ['company', 'name']

    def created_at_kst(self, obj):
        """한국 시간으로 생성일 표시"""
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    created_at_kst.short_description = '생성일시 (KST)'
    created_at_kst.admin_order_field = 'created_at'

    def updated_at_kst(self, obj):
        """한국 시간으로 수정일 표시"""
        if obj.updated_at:
            local_time = timezone.localtime(obj.updated_at)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    updated_at_kst.short_description = '수정일시 (KST)'
    updated_at_kst.admin_order_field = 'updated_at'


# ======================================================
# User Admin
# ======================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """사용자 관리자 페이지"""

    # 리스트 페이지
    list_display = ['username', 'email', 'company', 'department', 'role', 'status', 'is_active', 'created_at_kst']
    list_filter = ['role', 'status', 'is_active', 'is_staff', 'is_superuser', 'company', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-created_at']

    # 상세 페이지
    fieldsets = (
        ('기본 정보', {
            'fields': ('user_id', 'username', 'password_hash')
        }),
        ('개인 정보', {
            'fields': ('email', 'first_name', 'last_name')
        }),
        ('소속', {
            'fields': ('company', 'department')
        }),
        ('역할 및 상태', {
            'fields': ('role', 'status')
        }),
        ('권한', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('중요 날짜', {
            'fields': ('last_login_kst', 'date_joined_kst', 'created_at_kst', 'updated_at_kst')
        }),
    )

    # 추가 페이지
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password_hash',
                'company', 'department',
                'role', 'status',
                'is_active', 'is_staff'
            ),
        }),
    )

    # 읽기 전용 필드
    readonly_fields = ['user_id', 'last_login_kst', 'date_joined_kst', 'created_at_kst', 'updated_at_kst']

    def created_at_kst(self, obj):
        """한국 시간으로 생성일 표시"""
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    created_at_kst.short_description = '생성일시 (KST)'
    created_at_kst.admin_order_field = 'created_at'

    def updated_at_kst(self, obj):
        """한국 시간으로 수정일 표시"""
        if obj.updated_at:
            local_time = timezone.localtime(obj.updated_at)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    updated_at_kst.short_description = '수정일시 (KST)'
    updated_at_kst.admin_order_field = 'updated_at'

    def last_login_kst(self, obj):
        """한국 시간으로 마지막 로그인 표시"""
        if obj.last_login:
            local_time = timezone.localtime(obj.last_login)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    last_login_kst.short_description = '마지막 로그인 (KST)'
    last_login_kst.admin_order_field = 'last_login'

    def date_joined_kst(self, obj):
        """한국 시간으로 가입일 표시"""
        if obj.date_joined:
            local_time = timezone.localtime(obj.date_joined)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    date_joined_kst.short_description = '가입일 (KST)'
    date_joined_kst.admin_order_field = 'date_joined'


# ======================================================
# AdminRequest Admin
# ======================================================

@admin.register(AdminRequest)
class AdminRequestAdmin(admin.ModelAdmin):
    """통합 요청 관리자 페이지 (회원 승인, 부서 관리자 권한, 비밀번호 초기화)"""

    list_display = ['request_id', 'request_type', 'user', 'target_user', 'department', 'status', 'requested_at_kst', 'handled_by', 'handled_at_kst']
    list_filter = ['request_type', 'status', 'requested_at', 'handled_at']
    search_fields = ['user__username', 'target_user__username', 'department__name', 'comment']
    readonly_fields = ['request_id', 'requested_at_kst', 'handled_at_kst']
    ordering = ['-requested_at']

    def requested_at_kst(self, obj):
        """한국 시간으로 요청일시 표시"""
        if obj.requested_at:
            local_time = timezone.localtime(obj.requested_at)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    requested_at_kst.short_description = '요청일시 (KST)'
    requested_at_kst.admin_order_field = 'requested_at'

    def handled_at_kst(self, obj):
        """한국 시간으로 처리일시 표시"""
        if obj.handled_at:
            local_time = timezone.localtime(obj.handled_at)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    handled_at_kst.short_description = '처리일시 (KST)'
    handled_at_kst.admin_order_field = 'handled_at'

    fieldsets = (
        ('요청 기본 정보', {
            'fields': ('request_id', 'request_type', 'user', 'target_user', 'requested_at_kst')
        }),
        ('소속 정보', {
            'fields': ('company', 'department')
        }),
        ('처리 정보', {
            'fields': ('status', 'handled_by', 'handled_at_kst', 'comment')
        }),
    )


# Admin 사이트 커스터마이징
admin.site.site_header = 'Patent Analysis System 관리자'
admin.site.site_title = 'PatentAI Admin'
admin.site.index_title = '관리자 대시보드'
