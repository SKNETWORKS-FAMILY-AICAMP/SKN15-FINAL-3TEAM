"""
초기 슈퍼 관리자 및 회사/부서 설정 명령어
사용법: python manage.py setup_initial_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Company, Department

User = get_user_model()


class Command(BaseCommand):
    help = '초기 슈퍼 관리자 및 회사/부서 설정'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('    초기 슈퍼 관리자 및 회사 설정'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

        # =========================================
        # 1. 회사 정보 입력
        # =========================================
        self.stdout.write(self.style.WARNING('[1단계] 회사 정보 입력\n'))

        company_name = input('회사명을 입력하세요: ').strip()
        if not company_name:
            self.stdout.write(self.style.ERROR('❌ 회사명은 필수입니다.'))
            return

        company_domain = input('회사 도메인 (선택사항, 예: company.com): ').strip() or None

        # 회사 생성
        try:
            company, created = Company.objects.get_or_create(
                name=company_name,
                defaults={'domain': company_domain}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ 회사 "{company_name}" 생성 완료\n'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️  회사 "{company_name}"이(가) 이미 존재합니다.\n'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 회사 생성 실패: {str(e)}'))
            return

        # =========================================
        # 2. 부서 정보 입력
        # =========================================
        self.stdout.write(self.style.WARNING('[2단계] 부서 정보 입력\n'))
        self.stdout.write('부서명을 입력하세요 (여러 개 입력 가능, 완료하려면 엔터만 입력):')

        departments = []
        dept_count = 1
        while True:
            dept_name = input(f'  부서 #{dept_count}: ').strip()
            if not dept_name:
                if dept_count == 1:
                    self.stdout.write(self.style.WARNING('⚠️  부서를 하나 이상 입력해주세요.'))
                    continue
                break

            # 부서 생성
            try:
                dept, created = Department.objects.get_or_create(
                    company=company,
                    name=dept_name
                )
                if created:
                    departments.append(dept)
                    self.stdout.write(self.style.SUCCESS(f'     ✅ "{dept_name}" 추가됨'))
                else:
                    self.stdout.write(self.style.WARNING(f'     ⚠️  "{dept_name}"은(는) 이미 존재합니다'))
                dept_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'     ❌ 부서 생성 실패: {str(e)}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✅ 총 {len(departments)}개 부서 생성 완료\n'))

        # =========================================
        # 3. 슈퍼 관리자 정보 입력
        # =========================================
        self.stdout.write(self.style.WARNING('[3단계] 슈퍼 관리자 계정 생성\n'))

        username = input('관리자 사용자명 (Username): ').strip()
        if not username:
            self.stdout.write(self.style.ERROR('❌ 사용자명은 필수입니다.'))
            return

        # 중복 확인
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'❌ 사용자명 "{username}"이(가) 이미 존재합니다.'))
            return

        email = input('관리자 이메일 (Email): ').strip()
        if not email:
            self.stdout.write(self.style.ERROR('❌ 이메일은 필수입니다.'))
            return

        # 중복 확인
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f'❌ 이메일 "{email}"이(가) 이미 존재합니다.'))
            return

        first_name = input('이름 (First Name, 선택): ').strip() or ''
        last_name = input('성 (Last Name, 선택): ').strip() or ''

        # 비밀번호 입력
        import getpass
        password = getpass.getpass('비밀번호 (Password): ')
        if not password:
            self.stdout.write(self.style.ERROR('❌ 비밀번호는 필수입니다.'))
            return

        if len(password) < 8:
            self.stdout.write(self.style.ERROR('❌ 비밀번호는 최소 8자 이상이어야 합니다.'))
            return

        password_confirm = getpass.getpass('비밀번호 확인 (Password again): ')
        if password != password_confirm:
            self.stdout.write(self.style.ERROR('❌ 비밀번호가 일치하지 않습니다.'))
            return

        # 부서 선택 (선택사항)
        self.stdout.write(f'\n{company.name}의 부서 목록:')
        for idx, dept in enumerate(departments, 1):
            self.stdout.write(f'  {idx}. {dept.name}')

        dept_choice = input(f'\n관리자가 소속될 부서 번호 (1-{len(departments)}, 선택사항): ').strip()
        selected_dept = None
        if dept_choice:
            try:
                dept_idx = int(dept_choice) - 1
                if 0 <= dept_idx < len(departments):
                    selected_dept = departments[dept_idx]
                else:
                    self.stdout.write(self.style.WARNING('⚠️  잘못된 번호입니다. 부서 없이 진행합니다.'))
            except ValueError:
                self.stdout.write(self.style.WARNING('⚠️  잘못된 입력입니다. 부서 없이 진행합니다.'))

        # =========================================
        # 4. 슈퍼 관리자 생성
        # =========================================
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                company=company,
                department=selected_dept,
                first_name=first_name,
                last_name=last_name,
            )

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('='*60))
            self.stdout.write(self.style.SUCCESS('✅ 초기 설정 완료!'))
            self.stdout.write(self.style.SUCCESS('='*60))
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('[회사 정보]'))
            self.stdout.write(f'  회사명: {company.name}')
            if company.domain:
                self.stdout.write(f'  도메인: {company.domain}')
            self.stdout.write(f'  부서 수: {len(departments)}개')
            for dept in departments:
                self.stdout.write(f'    - {dept.name}')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('[관리자 계정]'))
            self.stdout.write(f'  사용자명: {username}')
            self.stdout.write(f'  이메일: {email}')
            if first_name or last_name:
                self.stdout.write(f'  이름: {last_name} {first_name}')
            self.stdout.write(f'  회사: {company.name}')
            if selected_dept:
                self.stdout.write(f'  부서: {selected_dept.name}')
            self.stdout.write(f'  역할: super_admin')
            self.stdout.write(f'  상태: active')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('[다음 단계]'))
            self.stdout.write('  1. Django 서버 실행:')
            self.stdout.write('     python manage.py runserver')
            self.stdout.write('')
            self.stdout.write('  2. 로그인 테스트:')
            self.stdout.write(f'     http://localhost:3000/login')
            self.stdout.write(f'     사용자명: {username}')
            self.stdout.write(f'     비밀번호: (방금 입력한 비밀번호)')
            self.stdout.write('')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ 슈퍼 관리자 생성 실패: {str(e)}'))
