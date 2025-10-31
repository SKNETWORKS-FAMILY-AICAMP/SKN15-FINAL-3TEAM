"""
API 데이터 직렬화 (Serializers)
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Company, Department, User, AdminRequest, SearchHistory


# ======================================================
# Company & Department Serializers
# ======================================================

class CompanySerializer(serializers.ModelSerializer):
    """회사 정보"""
    class Meta:
        model = Company
        fields = ['company_id', 'name', 'domain', 'created_at', 'updated_at']
        read_only_fields = ['company_id', 'created_at', 'updated_at']


class DepartmentSerializer(serializers.ModelSerializer):
    """부서 정보"""
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Department
        fields = ['department_id', 'company', 'company_name', 'name', 'created_at', 'updated_at']
        read_only_fields = ['department_id', 'created_at', 'updated_at']


# ======================================================
# User Serializers
# ======================================================

class UserSerializer(serializers.ModelSerializer):
    """사용자 정보 조회용"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'user_id', 'username', 'email',
            'company', 'company_name',
            'department', 'department_name',
            'role', 'status',
            'first_name', 'last_name', 'full_name',
            'is_active', 'created_at', 'last_login'
        ]
        read_only_fields = ['user_id', 'created_at', 'last_login']

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserDetailSerializer(serializers.ModelSerializer):
    """사용자 상세 정보"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'user_id', 'username', 'email',
            'company', 'company_name',
            'department', 'department_name',
            'role', 'status',
            'first_name', 'last_name', 'full_name',
            'is_active', 'is_staff', 'is_superuser',
            'created_at', 'updated_at', 'last_login', 'date_joined'
        ]
        read_only_fields = ['user_id', 'created_at', 'updated_at', 'last_login', 'date_joined']

    def get_full_name(self, obj):
        return obj.get_full_name()


# ======================================================
# Authentication Serializers
# ======================================================

class RegisterSerializer(serializers.ModelSerializer):
    """회원가입용 Serializer"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text='최소 8자 이상'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='비밀번호 확인'
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'company', 'department',
            'first_name', 'last_name'
        ]

    def validate_username(self, value):
        """username 유효성 및 중복 확인"""
        import re

        # 영어, 숫자, 언더스코어만 허용
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError('아이디는 영어, 숫자, 언더스코어(_)만 사용할 수 있습니다.')

        # 중복 확인
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('이미 존재하는 사용자명입니다.')

        return value

    def validate_email(self, value):
        """email 중복 확인"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('이미 사용 중인 이메일입니다.')
        return value

    def validate(self, attrs):
        """비밀번호 일치 확인"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': '비밀번호가 일치하지 않습니다.'
            })
        return attrs

    def create(self, validated_data):
        """사용자 생성 및 승인 요청 자동 생성"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            company=validated_data['company'],
            department=validated_data.get('department'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role='user',
            status='pending'  # 관리자 승인 대기 상태
        )

        # 회원가입 승인 요청 자동 생성
        from .models import AdminRequest
        AdminRequest.objects.create(
            request_type='user_approval',
            user=user,
            company=user.company,
            department=user.department,
            status='pending',
            comment='회원가입 승인 요청'
        )

        return user


class LoginSerializer(serializers.Serializer):
    """로그인용 Serializer"""
    username = serializers.CharField(required=True, help_text='사용자명')
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text='비밀번호'
    )


class PasswordChangeSerializer(serializers.Serializer):
    """비밀번호 변경용"""
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """새 비밀번호 일치 확인"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': '새 비밀번호가 일치하지 않습니다.'
            })
        return attrs

    def validate_old_password(self, value):
        """기존 비밀번호 확인"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('기존 비밀번호가 올바르지 않습니다.')
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    """사용자 정보 수정용"""
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'department']

    def validate_email(self, value):
        """이메일 중복 확인 (자신 제외)"""
        user = self.context['request'].user
        if User.objects.exclude(user_id=user.user_id).filter(email=value).exists():
            raise serializers.ValidationError('이미 사용 중인 이메일입니다.')
        return value


# ======================================================
# AdminRequest Serializers (통합 요청 관리)
# ======================================================

class AdminRequestSerializer(serializers.ModelSerializer):
    """통합 요청 조회 (회원 승인, 부서 관리자 권한, 비밀번호 초기화)"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    target_user_name = serializers.CharField(source='target_user.username', read_only=True, allow_null=True)
    target_user_email = serializers.CharField(source='target_user.email', read_only=True, allow_null=True)
    company_name = serializers.CharField(source='company.name', read_only=True, allow_null=True)
    department_name = serializers.CharField(source='department.name', read_only=True, allow_null=True)
    handled_by_name = serializers.CharField(source='handled_by.username', read_only=True, allow_null=True)
    request_type_display = serializers.CharField(source='get_request_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AdminRequest
        fields = [
            'request_id', 'request_type', 'request_type_display',
            'user', 'user_name', 'user_email',
            'target_user', 'target_user_name', 'target_user_email',
            'company', 'company_name',
            'department', 'department_name',
            'status', 'status_display',
            'requested_at', 'handled_by', 'handled_by_name',
            'handled_at', 'comment'
        ]
        read_only_fields = [
            'request_id', 'requested_at', 'handled_by',
            'handled_at', 'status'
        ]


class AdminRequestCreateSerializer(serializers.Serializer):
    """통합 요청 생성 (회원 승인, 부서 관리자 권한, 비밀번호 초기화)"""
    request_type = serializers.ChoiceField(
        choices=['user_approval', 'dept_admin', 'password_reset'],
        required=True
    )
    department_id = serializers.IntegerField(required=False, allow_null=True)
    target_user_id = serializers.UUIDField(required=False, allow_null=True)
    comment = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        """요청 타입별 필수 필드 검증"""
        request_type = data.get('request_type')

        if request_type == 'dept_admin' and not data.get('department_id'):
            raise serializers.ValidationError({
                'department_id': '부서 관리자 권한 요청 시 부서를 선택해야 합니다.'
            })

        if request_type == 'password_reset' and not data.get('target_user_id'):
            raise serializers.ValidationError({
                'target_user_id': '비밀번호 초기화 요청 시 대상 사용자를 선택해야 합니다.'
            })

        return data

    def create(self, validated_data):
        """요청 생성"""
        user = self.context['request'].user
        request_type = validated_data['request_type']

        # 중복 요청 확인
        existing_request = AdminRequest.objects.filter(
            user=user,
            request_type=request_type,
            status='pending'
        )

        if request_type == 'dept_admin' and validated_data.get('department_id'):
            existing_request = existing_request.filter(department_id=validated_data['department_id'])
        elif request_type == 'password_reset' and validated_data.get('target_user_id'):
            existing_request = existing_request.filter(target_user_id=validated_data['target_user_id'])

        if existing_request.exists():
            raise serializers.ValidationError('이미 처리 대기 중인 요청이 있습니다.')

        # 요청 생성
        request_data = {
            'user': user,
            'request_type': request_type,
            'comment': validated_data.get('comment', '')
        }

        if request_type == 'user_approval':
            request_data['company'] = user.company
            request_data['department'] = user.department
        elif request_type == 'dept_admin':
            from .models import Department
            department = Department.objects.get(department_id=validated_data['department_id'])
            request_data['company'] = user.company
            request_data['department'] = department
        elif request_type == 'password_reset':
            target_user = User.objects.get(user_id=validated_data['target_user_id'])
            request_data['target_user'] = target_user

        return AdminRequest.objects.create(**request_data)


class AdminRequestHandleSerializer(serializers.Serializer):
    """통합 요청 처리 (승인/거부)"""
    status = serializers.ChoiceField(
        choices=['approved', 'rejected'],
        required=True
    )
    comment = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    temp_password = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text='비밀번호 초기화 요청 승인 시 임시 비밀번호'
    )


# ======================================================
# Admin User Management Serializers (슈퍼 관리자 전용)
# ======================================================

class UserStatusUpdateSerializer(serializers.Serializer):
    """사용자 상태 변경 (슈퍼 관리자 전용)"""
    status = serializers.ChoiceField(
        choices=['active', 'pending', 'suspended'],
        required=True
    )


class UserRoleUpdateSerializer(serializers.Serializer):
    """사용자 역할 변경 (슈퍼 관리자 전용)"""
    role = serializers.ChoiceField(
        choices=['user', 'dept_admin', 'super_admin'],
        required=True
    )


# ======================================================
# 참고: 관리자 회원가입 기능은 제거되었습니다.
# 모든 사용자는 일반 회원가입(RegisterSerializer)을 통해 등록하고,
# 슈퍼 관리자가 필요 시 부서 관리자로 승격합니다.
# ======================================================


# ======================================================
# SearchHistory Serializers (공유 히스토리)
# ======================================================

class SearchHistorySerializer(serializers.ModelSerializer):
    """검색 히스토리 조회용 (통합 챗봇)"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = SearchHistory
        fields = [
            'history_id', 'company', 'company_name',
            'department', 'department_name',
            'query', 'results_count',
            'created_by', 'created_by_name',
            'created_at'
        ]
        read_only_fields = ['history_id', 'created_at']


class SearchHistoryCreateSerializer(serializers.ModelSerializer):
    """검색 히스토리 생성용 (통합 챗봇)"""

    class Meta:
        model = SearchHistory
        fields = ['query', 'results_count']

    def create(self, validated_data):
        """검색 히스토리 생성"""
        user = self.context['request'].user

        # 사용자의 회사/부서 정보 자동 설정
        history = SearchHistory.objects.create(
            company=user.company,
            department=user.department,
            created_by=user,
            **validated_data
        )

        return history
