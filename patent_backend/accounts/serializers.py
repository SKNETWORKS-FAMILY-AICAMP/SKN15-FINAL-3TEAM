"""
API 데이터 직렬화 (Serializers)
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Company, Department, User, AdminRequest, PasswordResetRequest, SearchHistory


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
        """username 중복 확인"""
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
        """사용자 생성"""
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
            status='active'  # 기본값: 활성화 (즉시 로그인 가능)
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
# AdminRequest Serializers
# ======================================================

class AdminRequestSerializer(serializers.ModelSerializer):
    """부서 관리자 권한 요청"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    handled_by_name = serializers.CharField(source='handled_by.username', read_only=True, allow_null=True)

    class Meta:
        model = AdminRequest
        fields = [
            'request_id', 'user', 'user_name',
            'company', 'company_name',
            'department', 'department_name',
            'requested_at', 'handled_by', 'handled_by_name',
            'handled_at', 'status', 'note'
        ]
        read_only_fields = [
            'request_id', 'requested_at', 'handled_by',
            'handled_at', 'status'
        ]


class AdminRequestCreateSerializer(serializers.ModelSerializer):
    """부서 관리자 권한 요청 생성"""
    class Meta:
        model = AdminRequest
        fields = ['department', 'note']

    def create(self, validated_data):
        """요청 생성"""
        user = self.context['request'].user

        # 이미 대기 중인 요청이 있는지 확인
        existing_request = AdminRequest.objects.filter(
            user=user,
            department=validated_data['department'],
            status='pending'
        ).first()

        if existing_request:
            raise serializers.ValidationError('이미 처리 대기 중인 요청이 있습니다.')

        # company 자동 설정
        return AdminRequest.objects.create(
            user=user,
            company=user.company,
            **validated_data
        )


class AdminRequestHandleSerializer(serializers.Serializer):
    """부서 관리자 권한 요청 처리 (승인/거부)"""
    status = serializers.ChoiceField(
        choices=['approved', 'rejected'],
        required=True
    )
    note = serializers.CharField(required=False, allow_blank=True)


# ======================================================
# PasswordResetRequest Serializers
# ======================================================

class PasswordResetRequestSerializer(serializers.ModelSerializer):
    """비밀번호 초기화 요청"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_department = serializers.CharField(source='user.department.name', read_only=True)

    class Meta:
        model = PasswordResetRequest
        fields = [
            'reset_id', 'user', 'user_name', 'user_email', 'user_department',
            'requested_by', 'requested_by_name',
            'status', 'requested_at', 'handled_at'
        ]
        read_only_fields = [
            'reset_id', 'requested_by',
            'status', 'requested_at', 'handled_at'
        ]


class PasswordResetRequestCreateSerializer(serializers.Serializer):
    """비밀번호 초기화 요청 생성 (슈퍼 관리자 전용)"""
    user_id = serializers.UUIDField(required=True)
    temp_password = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        help_text='임시 비밀번호 (최소 8자)'
    )

    def validate_user_id(self, value):
        """대상 사용자 확인"""
        try:
            user = User.objects.get(user_id=value)
            # 부서 관리자만 초기화 가능
            if user.role != 'dept_admin':
                raise serializers.ValidationError('부서 관리자만 비밀번호 초기화가 가능합니다.')
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError('존재하지 않는 사용자입니다.')

    def create(self, validated_data):
        """임시 비밀번호 발급"""
        user = User.objects.get(user_id=validated_data['user_id'])
        requested_by = self.context['request'].user
        temp_password = validated_data['temp_password']

        # 임시 비밀번호 설정
        user.set_password(temp_password)
        user.save()

        # 요청 기록 생성
        reset_request = PasswordResetRequest.objects.create(
            user=user,
            requested_by=requested_by,
            temp_password=temp_password,  # 평문 저장 (슈퍼 관리자가 전달해야 하므로)
            expires_at=timezone.now() + timedelta(days=7),  # 7일 후 만료
            status='completed',
            handled_at=timezone.now()
        )

        return reset_request


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
# Admin Registration Serializer (관리자 회원가입)
# ======================================================

class AdminRegisterSerializer(serializers.ModelSerializer):
    """관리자 회원가입용 Serializer (부서 관리자 전용)"""
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
        """username 중복 확인"""
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
        """부서 관리자 사용자 생성"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        # 부서 관리자로 생성 (일반 유저처럼 pending 상태, 즉시 로그인 가능)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            company=validated_data['company'],
            department=validated_data.get('department'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role='user',  # 초기에는 일반 유저로 생성
            status='active'  # 즉시 로그인 가능
        )

        # 관리자 권한 요청 자동 생성
        if validated_data.get('department'):
            AdminRequest.objects.create(
                user=user,
                company=validated_data['company'],
                department=validated_data['department'],
                note='관리자 회원가입 시 자동 생성된 권한 요청'
            )

        return user


# ======================================================
# SearchHistory Serializers (공유 히스토리)
# ======================================================

class SearchHistorySerializer(serializers.ModelSerializer):
    """검색 히스토리 조회용"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    search_type_display = serializers.CharField(source='get_search_type_display', read_only=True)

    class Meta:
        model = SearchHistory
        fields = [
            'history_id', 'company', 'company_name',
            'department', 'department_name',
            'query', 'search_type', 'search_type_display',
            'results_count', 'results_summary',
            'created_by', 'created_by_name',
            'created_at', 'is_shared'
        ]
        read_only_fields = ['history_id', 'created_at']


class SearchHistoryCreateSerializer(serializers.ModelSerializer):
    """검색 히스토리 생성용"""

    class Meta:
        model = SearchHistory
        fields = [
            'query', 'search_type', 'results_count',
            'results_summary', 'is_shared'
        ]

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
