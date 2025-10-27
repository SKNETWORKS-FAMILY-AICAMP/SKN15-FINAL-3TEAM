"""
accounts 앱 URL 설정
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # ======================================================
    # 인증 관련
    # ======================================================
    path('register/', views.register, name='register'),
    path('admin/register/', views.admin_register, name='admin-register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    # JWT 토큰 관리
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ======================================================
    # 사용자 정보
    # ======================================================
    path('me/', views.get_user_info, name='user-info'),
    path('me/update/', views.update_user_info, name='user-update'),
    path('change-password/', views.change_password, name='change-password'),

    # ======================================================
    # 회사 & 부서
    # ======================================================
    path('companies/', views.list_companies, name='list-companies'),
    path('departments/', views.list_departments, name='list-departments'),

    # ======================================================
    # 부서 관리자 권한 요청
    # ======================================================
    path('admin-requests/', views.list_admin_requests, name='list-admin-requests'),
    path('admin-requests/create/', views.request_admin_role, name='request-admin-role'),
    path('admin-requests/<int:request_id>/handle/', views.handle_admin_request, name='handle-admin-request'),

    # ======================================================
    # 비밀번호 초기화
    # ======================================================
    path('password-reset/', views.reset_password, name='reset-password'),
    path('password-resets/', views.list_password_resets, name='list-password-resets'),
    path('password-resets/request/', views.request_password_reset, name='request-password-reset'),
    path('password-resets/request-anonymous/', views.request_password_reset_anonymous, name='request-password-reset-anonymous'),

    # ======================================================
    # 사용자 관리 (관리자)
    # ======================================================
    path('users/', views.list_users, name='list-users'),
    path('users/<uuid:user_id>/status/', views.update_user_status, name='update-user-status'),
    path('users/<uuid:user_id>/role/', views.update_user_role, name='update-user-role'),
    path('users/<uuid:user_id>/reset-password/', views.dept_admin_reset_user_password, name='dept-admin-reset-password'),
    path('users/<uuid:user_id>/', views.delete_user, name='delete-user'),

    # ======================================================
    # SearchHistory (공유 히스토리)
    # ======================================================
    path('history/', views.search_history, name='search-history'),
    path('history/<uuid:history_id>/', views.delete_search_history, name='delete-search-history'),

    # ======================================================
    # 헬스체크
    # ======================================================
    path('health/', views.health_check, name='health-check'),
]
