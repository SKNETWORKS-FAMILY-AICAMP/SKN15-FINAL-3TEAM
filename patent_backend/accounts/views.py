"""
인증 및 사용자 관리 API Views
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone

from .models import User, Company, Department, AdminRequest, SearchHistory
from .serializers import (
    RegisterSerializer, LoginSerializer,
    UserSerializer, UserDetailSerializer,
    PasswordChangeSerializer, UserUpdateSerializer,
    CompanySerializer, DepartmentSerializer,
    AdminRequestSerializer, AdminRequestCreateSerializer, AdminRequestHandleSerializer,
    UserStatusUpdateSerializer, UserRoleUpdateSerializer,
    SearchHistorySerializer, SearchHistoryCreateSerializer,
)


# ======================================================
# 인증 API
# ======================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    회원가입 API

    POST /api/auth/register/
    {
        "username": "testuser",
        "email": "test@example.com",
        "password": "test1234",
        "password_confirm": "test1234",
        "company": 1,
        "department": 1,
        "first_name": "길동",
        "last_name": "홍"
    }
    """
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        try:
            with transaction.atomic():
                user = serializer.save()

                # JWT 토큰 생성
                refresh = RefreshToken.for_user(user)

                return Response({
                    'message': '회원가입이 완료되었습니다. 관리자 승인 후 사용 가능합니다.',
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': '회원가입 중 오류가 발생했습니다.',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ======================================================
# 참고: 관리자 회원가입 엔드포인트(admin_register)는 제거되었습니다.
# 모든 사용자는 register 엔드포인트로 가입합니다.
# ======================================================


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    로그인 API

    POST /api/auth/login/
    {
        "username": "testuser",
        "password": "test1234"
    }
    """
    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        # 사용자 조회 (is_active 여부와 관계없이)
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({
                'error': '사용자명 또는 비밀번호가 올바르지 않습니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # 비밀번호 확인
        if not user.check_password(password):
            return Response({
                'error': '사용자명 또는 비밀번호가 올바르지 않습니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # 계정 상태 확인
        if user.status == 'pending':
            return Response({
                'error': '승인되지 않은 계정입니다. 관리자에게 문의하세요.'
            }, status=status.HTTP_403_FORBIDDEN)

        if user.status == 'suspended':
            return Response({
                'error': '정지된 계정입니다. 관리자에게 문의하세요.'
            }, status=status.HTTP_403_FORBIDDEN)

        if not user.is_active:
            return Response({
                'error': '비활성화된 계정입니다.'
            }, status=status.HTTP_403_FORBIDDEN)

        # JWT 토큰 생성
        refresh = RefreshToken.for_user(user)

        # 마지막 로그인 시간 업데이트
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        return Response({
            'message': '로그인 성공',
            'user': UserDetailSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    로그아웃 API

    POST /api/auth/logout/
    {
        "refresh": "refresh_token_here"
    }
    """
    try:
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({
                'error': 'Refresh token이 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response({
            'message': '로그아웃 되었습니다.'
        }, status=status.HTTP_200_OK)

    except TokenError:
        return Response({
            'error': '유효하지 않은 토큰입니다.'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': '로그아웃 중 오류가 발생했습니다.',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ======================================================
# 사용자 정보 API
# ======================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    """현재 로그인한 사용자 정보 조회"""
    serializer = UserDetailSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user_info(request):
    """사용자 정보 수정"""
    user = request.user
    serializer = UserUpdateSerializer(
        user,
        data=request.data,
        context={'request': request},
        partial=(request.method == 'PATCH')
    )

    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': '사용자 정보가 수정되었습니다.',
            'user': UserDetailSerializer(user).data
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """비밀번호 변경"""
    serializer = PasswordChangeSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({
            'message': '비밀번호가 변경되었습니다.'
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ======================================================
# 회사 & 부서 API
# ======================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def list_companies(request):
    """회사 목록 조회"""
    companies = Company.objects.all()
    serializer = CompanySerializer(companies, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_departments(request):
    """부서 목록 조회 (회사별 필터링 가능)"""
    company_id = request.query_params.get('company_id')

    departments = Department.objects.all()
    if company_id:
        departments = departments.filter(company_id=company_id)

    serializer = DepartmentSerializer(departments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ======================================================
# 부서 관리자 권한 요청 API
# ======================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_admin_role(request):
    """부서 관리자 권한 요청"""
    serializer = AdminRequestCreateSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        admin_request = serializer.save()
        return Response({
            'message': '부서 관리자 권한 요청이 제출되었습니다.',
            'request': AdminRequestSerializer(admin_request).data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_admin_requests(request):
    """통합 요청 목록 조회 (회원 승인, 부서 관리자 권한, 비밀번호 초기화)"""
    user = request.user

    # 권한별 요청 조회 범위 설정
    if user.is_super_admin:
        # 슈퍼 관리자: 같은 회사의 모든 요청
        requests = AdminRequest.objects.filter(user__company=user.company)
    elif user.is_dept_admin:
        # 부서 관리자: 자신의 부서 + 자신이 요청한 것
        requests = AdminRequest.objects.filter(
            user__department=user.department
        ) | AdminRequest.objects.filter(user=user)
    else:
        # 일반 사용자: 자신의 요청만
        requests = AdminRequest.objects.filter(user=user)

    # 필터링
    status_filter = request.query_params.get('status')
    request_type_filter = request.query_params.get('request_type')

    if status_filter:
        requests = requests.filter(status=status_filter)
    if request_type_filter:
        requests = requests.filter(request_type=request_type_filter)

    # 부서 관리자는 비밀번호 초기화 요청 시 일반 유저의 요청만 조회
    if user.is_dept_admin and request_type_filter == 'password_reset':
        requests = requests.filter(user__role='user')

    serializer = AdminRequestSerializer(requests.distinct(), many=True)
    return Response({
        'count': requests.distinct().count(),
        'requests': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_admin_request(request, request_id):
    """통합 요청 처리 (회원 승인, 부서 관리자 권한, 비밀번호 초기화)"""
    user = request.user

    # 권한 확인 (슈퍼 관리자 또는 부서 관리자)
    if not (user.is_super_admin or user.is_dept_admin):
        return Response({
            'error': '관리자 권한이 필요합니다.'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        admin_request = AdminRequest.objects.get(request_id=request_id)
    except AdminRequest.DoesNotExist:
        return Response({
            'error': '요청을 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)

    # 이미 처리된 요청인지 확인
    if admin_request.status != 'pending':
        return Response({
            'error': '이미 처리된 요청입니다.'
        }, status=status.HTTP_400_BAD_REQUEST)

    serializer = AdminRequestHandleSerializer(data=request.data)

    if serializer.is_valid():
        with transaction.atomic():
            admin_request.status = serializer.validated_data['status']
            admin_request.handled_by = user
            admin_request.handled_at = timezone.now()
            if serializer.validated_data.get('comment'):
                admin_request.comment = serializer.validated_data['comment']
            admin_request.save()

            # 요청 타입별 처리
            if admin_request.status == 'approved':
                if admin_request.request_type == 'user_approval':
                    # 회원 승인: 사용자 활성화
                    target_user = admin_request.user
                    target_user.status = 'active'
                    target_user.save()

                elif admin_request.request_type == 'dept_admin':
                    # 부서 관리자 권한: 역할 및 상태 변경
                    target_user = admin_request.user
                    target_user.role = 'dept_admin'
                    target_user.status = 'active'
                    target_user.save()

                elif admin_request.request_type == 'password_reset':
                    # 비밀번호 초기화: 임시 비밀번호 설정
                    temp_password = serializer.validated_data.get('temp_password')
                    if not temp_password:
                        return Response({
                            'error': '비밀번호 초기화 승인 시 임시 비밀번호를 입력해야 합니다.'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    target_user = admin_request.target_user
                    target_user.set_password(temp_password)
                    target_user.save()

                    # 비밀번호 변경 시 comment에 기록
                    admin_request.comment = f"임시 비밀번호 발급 완료: {temp_password}"
                    admin_request.save()

        response_data = {
            'message': f'요청이 {"승인" if admin_request.status == "approved" else "거부"}되었습니다.',
            'request': AdminRequestSerializer(admin_request).data
        }

        # 비밀번호 초기화 승인 시 임시 비밀번호 반환
        if admin_request.request_type == 'password_reset' and admin_request.status == 'approved':
            response_data['temp_password'] = serializer.validated_data.get('temp_password')

        return Response(response_data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ======================================================
# 통합 요청 생성 API
# ======================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_admin_request(request):
    """통합 요청 생성 (회원 승인, 부서 관리자 권한, 비밀번호 초기화)"""
    serializer = AdminRequestCreateSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        admin_request = serializer.save()
        return Response({
            'message': '요청이 생성되었습니다.',
            'request': AdminRequestSerializer(admin_request).data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset_anonymous(request):
    """로그인하지 않은 사용자의 비밀번호 초기화 요청 (로그인 페이지에서 사용)"""
    username = request.data.get('username')
    email = request.data.get('email')
    company_id = request.data.get('company')
    department_id = request.data.get('department')

    # 필수 필드 확인
    if not all([username, email, company_id]):
        return Response({
            'error': '사용자명, 이메일, 회사 정보를 입력해주세요.'
        }, status=status.HTTP_400_BAD_REQUEST)

    # 사용자 확인
    try:
        user = User.objects.get(
            username=username,
            email=email,
            company_id=company_id
        )
        if department_id:
            if str(user.department_id) != str(department_id):
                raise User.DoesNotExist
    except User.DoesNotExist:
        return Response({
            'error': '입력하신 정보와 일치하는 사용자를 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)

    # 슈퍼 관리자는 요청 불가
    if user.is_super_admin:
        return Response({
            'error': '슈퍼 관리자는 비밀번호 초기화를 요청할 수 없습니다.'
        }, status=status.HTTP_403_FORBIDDEN)

    # 이미 대기 중인 요청이 있는지 확인
    existing_request = AdminRequest.objects.filter(
        user=user,
        target_user=user,
        request_type='password_reset',
        status='pending'
    ).first()

    if existing_request:
        return Response({
            'error': '이미 처리 대기 중인 비밀번호 초기화 요청이 있습니다.'
        }, status=status.HTTP_400_BAD_REQUEST)

    # 새로운 요청 생성
    reset_request = AdminRequest.objects.create(
        user=user,
        target_user=user,
        request_type='password_reset',
        status='pending',
        comment='로그인 페이지에서 요청됨'
    )

    # 요청 대상 설명
    target_admin = "부서 관리자" if user.role == 'user' else "슈퍼 관리자"

    return Response({
        'message': f'비밀번호 초기화 요청이 {target_admin}에게 전달되었습니다.'
    }, status=status.HTTP_201_CREATED)


# ======================================================
# 사용자 관리 API (슈퍼 관리자 전용)
# ======================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
    """사용자 목록 조회"""
    user = request.user

    # 권한 확인
    if not (user.is_super_admin or user.is_dept_admin):
        return Response({
            'error': '관리자 권한이 필요합니다.'
        }, status=status.HTTP_403_FORBIDDEN)

    # 슈퍼 관리자는 같은 회사의 사용자만 조회
    if user.is_super_admin:
        users = User.objects.filter(company=user.company)
    # 부서 관리자는 자신의 부서만 조회
    elif user.is_dept_admin:
        users = User.objects.filter(department=user.department)
    else:
        users = User.objects.none()

    # 필터링
    company_id = request.query_params.get('company')
    department_id = request.query_params.get('department')
    role = request.query_params.get('role')
    status_filter = request.query_params.get('status')

    if company_id:
        users = users.filter(company_id=company_id)
    if department_id:
        users = users.filter(department_id=department_id)
    if role:
        users = users.filter(role=role)
    if status_filter:
        users = users.filter(status=status_filter)

    serializer = UserSerializer(users, many=True)
    return Response({
        'count': users.count(),
        'users': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user_status(request, user_id):
    """사용자 상태 변경 (슈퍼 관리자 및 부서 관리자)"""
    user = request.user

    # 관리자 권한 확인
    if not (user.is_super_admin or user.is_dept_admin):
        return Response({
            'error': '관리자 권한이 필요합니다.'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        target_user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return Response({
            'error': '사용자를 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)

    # 자기 자신은 상태 변경 불가
    if target_user.user_id == user.user_id:
        return Response({
            'error': '자기 자신의 상태를 변경할 수 없습니다.'
        }, status=status.HTTP_400_BAD_REQUEST)

    # 슈퍼 관리자는 상태 변경 불가
    if target_user.is_super_admin:
        return Response({
            'error': '슈퍼 관리자의 상태를 변경할 수 없습니다.'
        }, status=status.HTTP_403_FORBIDDEN)

    # 권한별 변경 범위 확인
    if user.is_super_admin:
        # 슈퍼 관리자: 같은 회사의 사용자만 변경 가능
        if target_user.company != user.company:
            return Response({
                'error': '같은 회사의 사용자만 변경할 수 있습니다.'
            }, status=status.HTTP_403_FORBIDDEN)
    elif user.is_dept_admin:
        # 부서 관리자: 같은 부서의 일반 사용자만 변경 가능
        if target_user.department != user.department:
            return Response({
                'error': '같은 부서의 사용자만 변경할 수 있습니다.'
            }, status=status.HTTP_403_FORBIDDEN)
        if target_user.is_dept_admin:
            return Response({
                'error': '부서 관리자의 상태를 변경할 수 없습니다.'
            }, status=status.HTTP_403_FORBIDDEN)

    serializer = UserStatusUpdateSerializer(data=request.data)

    if serializer.is_valid():
        target_user.status = serializer.validated_data['status']
        target_user.save()

        return Response({
            'message': '사용자 상태가 변경되었습니다.',
            'user': UserSerializer(target_user).data
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user_role(request, user_id):
    """사용자 역할 변경 (슈퍼 관리자 전용)"""
    if not request.user.is_super_admin:
        return Response({
            'error': '슈퍼 관리자 권한이 필요합니다.'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        target_user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return Response({
            'error': '사용자를 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)

    serializer = UserRoleUpdateSerializer(data=request.data)

    if serializer.is_valid():
        target_user.role = serializer.validated_data['role']
        target_user.save()

        return Response({
            'message': '사용자 역할이 변경되었습니다.',
            'user': UserSerializer(target_user).data
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    """사용자 삭제 (슈퍼 관리자 및 부서 관리자)"""
    user = request.user

    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"삭제 요청: user_id={user_id}, requester={user.username}, role={user.role}")

    # 관리자 권한 확인
    if not (user.is_super_admin or user.is_dept_admin):
        logger.warning(f"권한 없음: {user.username}")
        return Response({
            'error': '관리자 권한이 필요합니다.'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        target_user = User.objects.get(user_id=user_id)
        logger.info(f"대상 사용자: {target_user.username}, role={target_user.role}, status={target_user.status}")

        # 자기 자신은 삭제 불가
        if target_user.user_id == user.user_id:
            logger.warning(f"본인 계정 삭제 시도: {user.username}")
            return Response({
                'error': '자기 자신을 삭제할 수 없습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 슈퍼 관리자는 삭제 불가
        if target_user.is_super_admin:
            logger.warning(f"슈퍼 관리자 삭제 시도: {target_user.username}")
            return Response({
                'error': '슈퍼 관리자는 삭제할 수 없습니다.'
            }, status=status.HTTP_403_FORBIDDEN)

        # 권한별 삭제 범위 확인
        if user.is_super_admin:
            # 슈퍼 관리자: 같은 회사의 사용자만 삭제 가능
            if target_user.company != user.company:
                logger.warning(f"다른 회사 사용자 삭제 시도")
                return Response({
                    'error': '같은 회사의 사용자만 삭제할 수 있습니다.'
                }, status=status.HTTP_403_FORBIDDEN)
        elif user.is_dept_admin:
            # 부서 관리자: 같은 부서의 일반 사용자만 삭제 가능
            if target_user.department != user.department:
                logger.warning(f"다른 부서 사용자 삭제 시도")
                return Response({
                    'error': '같은 부서의 사용자만 삭제할 수 있습니다.'
                }, status=status.HTTP_403_FORBIDDEN)
            if target_user.is_dept_admin:
                logger.warning(f"부서 관리자 삭제 시도: {target_user.username}")
                return Response({
                    'error': '부서 관리자는 삭제할 수 없습니다.'
                }, status=status.HTTP_403_FORBIDDEN)

        username = target_user.username
        user_id_to_delete = target_user.user_id

        # managed=False 테이블이므로 SQL로 직접 삭제
        from django.db import connection
        with connection.cursor() as cursor:
            # 1. 먼저 관련된 토큰들 삭제 (JWT 블랙리스트)
            cursor.execute('DELETE FROM token_blacklist_outstandingtoken WHERE user_id = %s', [user_id_to_delete])
            logger.info(f"토큰 삭제 완료: {username}")

            # 2. admin_request 삭제
            cursor.execute('DELETE FROM admin_request WHERE user_id = %s', [user_id_to_delete])
            logger.info(f"관리자 요청 삭제 완료: {username}")

            # 3. password_reset_request 삭제
            cursor.execute('DELETE FROM password_reset_request WHERE user_id = %s', [user_id_to_delete])
            logger.info(f"비밀번호 초기화 요청 삭제 완료: {username}")

            # 4. 마지막으로 사용자 삭제
            cursor.execute('DELETE FROM "user" WHERE user_id = %s', [user_id_to_delete])

        logger.info(f"사용자 삭제 완료: {username}")

        return Response({
            'message': f'사용자 {username}이(가) 삭제되었습니다.'
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        logger.error(f"사용자를 찾을 수 없음: {user_id}")
        return Response({
            'error': '사용자를 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"삭제 중 오류 발생: {str(e)}")
        return Response({
            'error': f'삭제 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ======================================================
# 부서 관리자용 비밀번호 초기화
# ======================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dept_admin_reset_user_password(request, user_id):
    """부서 관리자가 일반 사용자 비밀번호 초기화"""
    admin = request.user

    # 부서 관리자 또는 슈퍼 관리자 권한 확인
    if not (admin.is_dept_admin or admin.is_super_admin):
        return Response({
            'error': '관리자 권한이 필요합니다.'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        # 대상 사용자
        target_user = User.objects.get(user_id=user_id)

        # 권한별 확인
        if admin.is_dept_admin:
            # 부서 관리자: 같은 부서 확인
            if target_user.department != admin.department:
                return Response({
                    'error': '같은 부서의 사용자만 비밀번호를 초기화할 수 있습니다.'
                }, status=status.HTTP_403_FORBIDDEN)
            # 부서 관리자는 일반 사용자만 초기화 가능
            if target_user.role != 'user':
                return Response({
                    'error': '일반 사용자만 비밀번호를 초기화할 수 있습니다.'
                }, status=status.HTTP_403_FORBIDDEN)
        elif admin.is_super_admin:
            # 슈퍼 관리자: 같은 회사 확인
            if target_user.company != admin.company:
                return Response({
                    'error': '같은 회사의 사용자만 비밀번호를 초기화할 수 있습니다.'
                }, status=status.HTTP_403_FORBIDDEN)
            # 슈퍼 관리자는 일반 사용자와 부서 관리자 모두 초기화 가능
            if target_user.is_super_admin:
                return Response({
                    'error': '슈퍼 관리자는 비밀번호를 초기화할 수 없습니다.'
                }, status=status.HTTP_403_FORBIDDEN)

        # 임시 비밀번호 가져오기
        temp_password = request.data.get('temp_password')
        if not temp_password or len(temp_password) < 8:
            return Response({
                'error': '임시 비밀번호는 최소 8자 이상이어야 합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 임시 비밀번호 설정
        target_user.set_password(temp_password)
        target_user.save()

        # 해당 사용자의 대기 중인 비밀번호 초기화 요청을 완료 처리
        AdminRequest.objects.filter(
            target_user=target_user,
            request_type='password_reset',
            status='pending'
        ).update(
            status='approved',
            handled_by=admin,
            handled_at=timezone.now(),
            comment=f'임시 비밀번호 발급 완료: {temp_password}'
        )

        return Response({
            'message': '비밀번호가 초기화되었습니다.',
            'temp_password': temp_password,
            'user': UserSerializer(target_user).data
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'error': '사용자를 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)


# ======================================================
# SearchHistory API (공유 히스토리)
# ======================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def search_history(request):
    """검색 히스토리 목록 조회 및 생성"""
    user = request.user

    if request.method == 'GET':
        # 필터 옵션
        my_only = request.query_params.get('my', 'false').lower() == 'true'

        if my_only:
            # 내가 생성한 히스토리만
            histories = SearchHistory.objects.filter(created_by=user)
        else:
            # 부서 전체 공유 히스토리 (통합 챗봇 - 모든 검색 공유)
            histories = SearchHistory.objects.filter(
                company=user.company,
                department=user.department
            )

        serializer = SearchHistorySerializer(histories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        # 히스토리 생성
        serializer = SearchHistoryCreateSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            history = serializer.save()
            return Response(
                SearchHistorySerializer(history).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_search_history(request, history_id):
    """검색 히스토리 삭제 (자신이 생성한 것만)"""
    user = request.user

    try:
        history = SearchHistory.objects.get(history_id=history_id)

        # 자신이 생성한 히스토리만 삭제 가능
        if history.created_by != user:
            return Response({
                'error': '자신이 생성한 히스토리만 삭제할 수 있습니다.'
            }, status=status.HTTP_403_FORBIDDEN)

        history.delete()

        return Response({
            'message': '히스토리가 삭제되었습니다.'
        }, status=status.HTTP_200_OK)

    except SearchHistory.DoesNotExist:
        return Response({
            'error': '히스토리를 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)


# ======================================================
# 헬스체크 API
# ======================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """API 서버 상태 확인"""
    return Response({
        'status': 'ok',
        'message': 'Patent Analysis API is running'
    }, status=status.HTTP_200_OK)
