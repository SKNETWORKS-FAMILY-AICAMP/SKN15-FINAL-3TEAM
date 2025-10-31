"""
새로운 사용자 관리 시스템 모델
- Company (회사)
- Department (부서)
- User (사용자)
- AdminRequest (통합 요청 관리: 회원 승인, 부서 관리자 권한, 비밀번호 초기화)
- SearchHistory (검색 히스토리)
"""

import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone


# ======================================================
# Company 모델
# ======================================================

class Company(models.Model):
    """회사 정보"""
    company_id = models.AutoField(primary_key=True)
    name = models.CharField('회사명', max_length=255, unique=True)
    domain = models.CharField('도메인', max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        db_table = 'company'
        managed = False  # PostgreSQL에서 직접 관리
        verbose_name = '회사'
        verbose_name_plural = '회사 목록'
        ordering = ['name']

    def __str__(self):
        return self.name


# ======================================================
# Department 모델
# ======================================================

class Department(models.Model):
    """부서 정보"""
    department_id = models.AutoField(primary_key=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        db_column='company_id',
        related_name='departments',
        verbose_name='회사'
    )
    name = models.CharField('부서명', max_length=255)
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        db_table = 'department'
        managed = False
        verbose_name = '부서'
        verbose_name_plural = '부서 목록'
        unique_together = [['company', 'name']]  # 같은 회사 내 부서명 중복 불가
        ordering = ['company', 'name']

    def __str__(self):
        return f"{self.company.name} - {self.name}"


# ======================================================
# User Manager
# ======================================================

class UserManager(BaseUserManager):
    """사용자 생성 및 관리"""

    def create_user(self, username, email, password=None, **extra_fields):
        """일반 사용자 생성"""
        if not username:
            raise ValueError('username은 필수입니다')
        if not email:
            raise ValueError('email은 필수입니다')

        email = self.normalize_email(email)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('status', 'pending')  # 기본값: 승인 대기
        extra_fields.setdefault('role', 'user')  # 기본값: 일반 사용자

        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)  # 비밀번호 해싱
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """슈퍼 관리자 생성"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('status', 'active')
        extra_fields.setdefault('role', 'super_admin')

        return self.create_user(username, email, password, **extra_fields)


# ======================================================
# User 모델
# ======================================================

class User(AbstractBaseUser, PermissionsMixin):
    """사용자 정보"""

    # 역할 선택지
    ROLE_CHOICES = [
        ('user', '일반 사용자'),
        ('dept_admin', '부서 관리자'),
        ('super_admin', '슈퍼 관리자'),
    ]

    # 상태 선택지
    STATUS_CHOICES = [
        ('active', '활성'),
        ('pending', '승인 대기'),
        ('suspended', '정지'),
    ]

    # 기본 필드
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField('사용자명', max_length=150, unique=True)
    email = models.EmailField('이메일', max_length=254, unique=True)
    password_hash = models.CharField('비밀번호', max_length=255, db_column='password_hash')

    # 외래키
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        db_column='company_id',
        related_name='users',
        verbose_name='회사'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        db_column='department_id',
        related_name='users',
        verbose_name='부서',
        null=True,
        blank=True
    )

    # 역할 및 상태
    role = models.CharField('역할', max_length=20, choices=ROLE_CHOICES, default='user')
    status = models.CharField('상태', max_length=20, choices=STATUS_CHOICES, default='pending')

    # Django 필수 필드 (role/status와 자동 동기화)
    first_name = models.CharField('이름', max_length=150, blank=True, default='')
    last_name = models.CharField('성', max_length=150, blank=True, default='')
    is_staff = models.BooleanField('스태프 권한', default=False, help_text='role에서 자동 동기화')
    is_active = models.BooleanField('활성 상태', default=True, help_text='status에서 자동 동기화')
    is_superuser = models.BooleanField('슈퍼유저 권한', default=False, help_text='role에서 자동 동기화')
    last_login = models.DateTimeField('마지막 로그인', blank=True, null=True)
    date_joined = models.DateTimeField('가입일', default=timezone.now)

    # 타임스탬프
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    # UserManager 연결
    objects = UserManager()

    # Django 인증 설정
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    password = None  # password_hash 사용

    class Meta:
        db_table = 'user'
        managed = False
        verbose_name = '사용자'
        verbose_name_plural = '사용자 목록'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def get_full_name(self):
        """전체 이름"""
        return f"{self.last_name}{self.first_name}".strip() or self.username

    def get_short_name(self):
        """짧은 이름"""
        return self.first_name or self.username

    @property
    def is_dept_admin(self):
        """부서 관리자 여부"""
        return self.role == 'dept_admin'

    @property
    def is_super_admin(self):
        """슈퍼 관리자 여부"""
        return self.role == 'super_admin' or self.is_superuser

    def set_password(self, raw_password):
        """비밀번호 설정 (해싱)"""
        from django.contrib.auth.hashers import make_password
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        """비밀번호 확인"""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password_hash)

    def save(self, *args, **kwargs):
        """저장 시 role/status를 기반으로 Django 필드 자동 동기화"""
        # role에서 is_staff, is_superuser 자동 동기화
        self.is_staff = self.role in ['super_admin', 'dept_admin']
        self.is_superuser = self.role == 'super_admin'

        # status에서 is_active 자동 동기화
        self.is_active = self.status == 'active'

        super().save(*args, **kwargs)


# ======================================================
# AdminRequest 모델 (통합 요청 관리)
# ======================================================

class AdminRequest(models.Model):
    """관리자 권한 및 비밀번호 초기화 요청 통합 테이블"""

    # 요청 타입 선택지
    REQUEST_TYPE_CHOICES = [
        ('user_approval', '회원 승인 요청'),
        ('dept_admin', '부서 관리자 권한 요청'),
        ('password_reset', '비밀번호 초기화 요청'),
    ]

    # 상태 선택지
    STATUS_CHOICES = [
        ('pending', '대기 중'),
        ('approved', '승인됨'),
        ('rejected', '거부됨'),
    ]

    request_id = models.AutoField(primary_key=True)

    # 요청 타입 (신규 컬럼)
    request_type = models.CharField(
        '요청 타입',
        max_length=20,
        choices=REQUEST_TYPE_CHOICES,
        default='user_approval'
    )

    # 요청자 (본인)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        related_name='admin_requests',
        verbose_name='요청자'
    )

    # 요청 대상자 (비밀번호 초기화 시 사용, 본인 요청 시 user와 동일)
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='target_user_id',
        related_name='targeted_requests',
        verbose_name='대상자',
        null=True,
        blank=True
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        db_column='company_id',
        related_name='admin_requests',
        verbose_name='회사',
        null=True,
        blank=True
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        db_column='department_id',
        related_name='admin_requests',
        verbose_name='관리할 부서',
        null=True,
        blank=True
    )

    # 상태 및 타임스탬프
    status = models.CharField('상태', max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField('요청일', auto_now_add=True)

    # 처리자 정보
    handled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_column='handled_by',
        related_name='handled_admin_requests',
        verbose_name='처리자',
        null=True,
        blank=True
    )
    handled_at = models.DateTimeField('처리일', null=True, blank=True)

    # 비고 (거부 사유 등)
    comment = models.TextField('비고', null=True, blank=True)

    class Meta:
        db_table = 'admin_request'
        managed = False
        verbose_name = '관리 요청'
        verbose_name_plural = '관리 요청 목록'
        ordering = ['-requested_at']

    def __str__(self):
        type_display = self.get_request_type_display()
        if self.request_type == 'password_reset' and self.target_user:
            return f"{self.user.username} → {self.target_user.username} 비밀번호 초기화 ({self.get_status_display()})"
        elif self.department:
            return f"{self.user.username} - {type_display} ({self.get_status_display()})"
        return f"{self.user.username} - {type_display} ({self.get_status_display()})"


# ======================================================
# SearchHistory 모델 (공유 히스토리)
# ======================================================

class SearchHistory(models.Model):
    """검색 히스토리 - 회사/부서별 공유 (통합 챗봇용)"""

    history_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='회사')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True, verbose_name='부서')

    # 검색 정보
    query = models.TextField('검색어')
    search_type = models.CharField('검색 유형', max_length=50, choices=[
        ('patent', '특허'),
        ('paper', '논문'),
        ('reject', '거절결정'),
        ('law', '특허법'),
        ('integrated', '통합검색'),
    ])
    results_count = models.IntegerField('결과 개수', default=0)
    results_summary = models.JSONField('결과 요약', null=True, blank=True)

    # 메타 정보
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='작성자')
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    is_shared = models.BooleanField('부서 공유', default=True, help_text='True면 같은 부서 전체 공유')

    class Meta:
        db_table = 'search_history'
        verbose_name = '검색 히스토리'
        verbose_name_plural = '검색 히스토리 목록'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'department', '-created_at']),
            models.Index(fields=['created_by', '-created_at']),
        ]

    def __str__(self):
        return f"{self.query} - {self.created_by.username if self.created_by else 'Unknown'}"
