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
    # admin/register 엔드포인트는 제거되었습니다. (모든 사용자는 일반 회원가입 사용)
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
    # 통합 요청 관리 (회원 승인, 부서 관리자 권한, 비밀번호 초기화)
    # ======================================================
    path('admin-requests/', views.list_admin_requests, name='list-admin-requests'),
    path('admin-requests/create/', views.create_admin_request, name='create-admin-request'),
    path('admin-requests/<int:request_id>/handle/', views.handle_admin_request, name='handle-admin-request'),

    # 하위 호환성을 위한 별칭 (기존 프론트엔드 코드가 이 URL을 사용할 경우)
    path('admin-requests/request-admin-role/', views.create_admin_request, name='request-admin-role'),
    path('password-resets/request/', views.create_admin_request, name='request-password-reset'),
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
