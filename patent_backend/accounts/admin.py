"""
Django Admin 설정
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Company, Department, User, AdminRequest, PasswordResetRequest


# ======================================================
# Company Admin
# ======================================================

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """회사 관리자 페이지"""
    list_display = ['company_id', 'name', 'domain', 'created_at']
    search_fields = ['name', 'domain']
    readonly_fields = ['company_id', 'created_at', 'updated_at']
    ordering = ['name']


# ======================================================
# Department Admin
# ======================================================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """부서 관리자 페이지"""
    list_display = ['department_id', 'company', 'name', 'created_at']
    list_filter = ['company']
    search_fields = ['name', 'company__name']
    readonly_fields = ['department_id', 'created_at', 'updated_at']
    ordering = ['company', 'name']


# ======================================================
# User Admin
# ======================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """사용자 관리자 페이지"""

    # 리스트 페이지
    list_display = ['username', 'email', 'company', 'department', 'role', 'status', 'is_active', 'created_at']
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
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
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
    readonly_fields = ['user_id', 'last_login', 'date_joined', 'created_at', 'updated_at']


# ======================================================
# AdminRequest Admin
# ======================================================

@admin.register(AdminRequest)
class AdminRequestAdmin(admin.ModelAdmin):
    """부서 관리자 권한 요청 관리자 페이지"""

    list_display = ['request_id', 'user', 'department', 'status', 'requested_at', 'handled_by', 'handled_at']
    list_filter = ['status', 'requested_at', 'handled_at']
    search_fields = ['user__username', 'department__name', 'note']
    readonly_fields = ['request_id', 'requested_at', 'handled_at']
    ordering = ['-requested_at']

    fieldsets = (
        ('요청 정보', {
            'fields': ('request_id', 'user', 'department', 'requested_at')
        }),
        ('처리 정보', {
            'fields': ('status', 'handled_by', 'handled_at', 'note')
        }),
    )


# ======================================================
# PasswordResetRequest Admin
# ======================================================

@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    """비밀번호 초기화 요청 관리자 페이지"""

    list_display = ['reset_id', 'user', 'requested_by', 'status', 'requested_at', 'handled_at']
    list_filter = ['status', 'requested_at']
    search_fields = ['user__username', 'requested_by__username']
    readonly_fields = ['reset_id', 'requested_at', 'handled_at']
    ordering = ['-requested_at']

    fieldsets = (
        ('대상 사용자', {
            'fields': ('reset_id', 'user')
        }),
        ('요청 정보', {
            'fields': ('requested_by', 'requested_at')
        }),
        ('처리 정보', {
            'fields': ('status', 'handled_at')
        }),
    )


# Admin 사이트 커스터마이징
admin.site.site_header = 'Patent Analysis System 관리자'
admin.site.site_title = 'PatentAI Admin'
admin.site.index_title = '관리자 대시보드'
