#!/usr/bin/env python
"""
RDS 슈퍼 관리자 자동 생성 스크립트

사용법:
1. 환경 변수 설정:
   export SUPER_USERNAME=admin
   export SUPER_EMAIL=admin@example.com
   export SUPER_PASSWORD=secure_password
   export SUPER_COMPANY_NAME=회사명
   export SUPER_COMPANY_DOMAIN=example.com  # 선택사항
   export SUPER_DEPARTMENT_NAME=개발팀  # 선택사항
   export SUPER_FIRST_NAME=관리자  # 선택사항
   export SUPER_LAST_NAME=시스템  # 선택사항

2. 스크립트 실행:
   python create_rds_superuser.py

3. 또는 Django 설정 로드 후 실행:
   python manage.py shell < create_rds_superuser.py
"""

import os
import sys
import django

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User, Company, Department
from django.db import transaction


def create_superuser_from_env():
    """환경 변수에서 값을 읽어 슈퍼 관리자 생성"""

    # 필수 환경 변수 확인
    required_vars = ['SUPER_USERNAME', 'SUPER_EMAIL', 'SUPER_PASSWORD', 'SUPER_COMPANY_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ 다음 환경 변수가 필요합니다: {', '.join(missing_vars)}")
        print("\n설정 예시:")
        print("  export SUPER_USERNAME=admin")
        print("  export SUPER_EMAIL=admin@example.com")
        print("  export SUPER_PASSWORD=secure_password")
        print("  export SUPER_COMPANY_NAME=회사명")
        sys.exit(1)

    # 환경 변수 읽기
    username = os.getenv('SUPER_USERNAME')
    email = os.getenv('SUPER_EMAIL')
    password = os.getenv('SUPER_PASSWORD')
    company_name = os.getenv('SUPER_COMPANY_NAME')
    company_domain = os.getenv('SUPER_COMPANY_DOMAIN')
    department_name = os.getenv('SUPER_DEPARTMENT_NAME')
    first_name = os.getenv('SUPER_FIRST_NAME', '관리자')
    last_name = os.getenv('SUPER_LAST_NAME', '시스템')

    print("="*60)
    print("RDS 슈퍼 관리자 생성 시작")
    print("="*60)
    print(f"사용자명: {username}")
    print(f"이메일: {email}")
    print(f"회사명: {company_name}")
    if company_domain:
        print(f"도메인: {company_domain}")
    if department_name:
        print(f"부서명: {department_name}")
    print("="*60)

    try:
        with transaction.atomic():
            # 1. 회사 생성 또는 가져오기
            print(f"\n[1/4] 회사 확인 중...")
            company, created = Company.objects.get_or_create(
                name=company_name,
                defaults={'domain': company_domain}
            )
            if created:
                print(f"✅ 회사 '{company_name}' 생성 완료")
            else:
                print(f"✅ 기존 회사 '{company_name}' 사용")

            # 2. 부서 생성 또는 가져오기 (선택사항)
            department = None
            if department_name:
                print(f"\n[2/4] 부서 확인 중...")
                department, created = Department.objects.get_or_create(
                    company=company,
                    name=department_name
                )
                if created:
                    print(f"✅ 부서 '{department_name}' 생성 완료")
                else:
                    print(f"✅ 기존 부서 '{department_name}' 사용")
            else:
                print(f"\n[2/4] 부서 설정 건너뛰기")

            # 3. 사용자명 중복 확인
            print(f"\n[3/4] 사용자 중복 확인 중...")
            if User.objects.filter(username=username).exists():
                print(f"❌ 사용자명 '{username}'이(가) 이미 존재합니다.")
                print("   다른 사용자명을 사용하거나 기존 사용자를 삭제해주세요.")
                sys.exit(1)

            if User.objects.filter(email=email).exists():
                print(f"❌ 이메일 '{email}'이(가) 이미 존재합니다.")
                print("   다른 이메일을 사용하거나 기존 사용자를 삭제해주세요.")
                sys.exit(1)

            print("✅ 사용자명/이메일 사용 가능")

            # 4. 슈퍼 관리자 생성
            print(f"\n[4/4] 슈퍼 관리자 생성 중...")
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                company=company,
                department=department,
                first_name=first_name,
                last_name=last_name,
            )

            print("\n" + "="*60)
            print("✅ 슈퍼 관리자 생성 완료!")
            print("="*60)
            print(f"사용자 ID: {user.user_id}")
            print(f"사용자명: {user.username}")
            print(f"이메일: {user.email}")
            print(f"이름: {user.get_full_name()}")
            print(f"회사: {user.company.name}")
            if user.department:
                print(f"부서: {user.department.name}")
            print(f"역할: {user.get_role_display()}")
            print(f"상태: {user.get_status_display()}")
            print("="*60)
            print("\n로그인 정보:")
            print(f"  URL: http://your-frontend-url/login")
            print(f"  사용자명: {username}")
            print(f"  비밀번호: (환경 변수에 설정한 비밀번호)")
            print("="*60)

    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    create_superuser_from_env()
