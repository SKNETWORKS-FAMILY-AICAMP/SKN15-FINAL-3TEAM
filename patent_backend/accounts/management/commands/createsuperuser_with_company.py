"""
커스텀 슈퍼 관리자 생성 명령어 (Company 필수)
사용법: python manage.py createsuperuser_with_company
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Company, Department

User = get_user_model()


class Command(BaseCommand):
    help = '회사 정보를 포함한 슈퍼 관리자 계정 생성'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== 슈퍼 관리자 계정 생성 ===\n'))

        # 회사 목록 표시
        self.stdout.write(self.style.WARNING('사용 가능한 회사:'))
        companies = Company.objects.all()
        for c in companies:
            self.stdout.write(f'  ID: {c.company_id} - {c.name}')

        if not companies.exists():
            self.stdout.write(self.style.ERROR('\n❌ 회사가 없습니다!'))
            self.stdout.write('먼저 회사를 생성하세요.')
            return

        self.stdout.write('')

        # 사용자 입력
        username = input('사용자명 (Username): ').strip()
        if not username:
            self.stdout.write(self.style.ERROR('사용자명은 필수입니다.'))
            return

        # 중복 확인
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'❌ 사용자명 "{username}"이(가) 이미 존재합니다.'))
            return

        email = input('이메일 (Email): ').strip()
        if not email:
            self.stdout.write(self.style.ERROR('이메일은 필수입니다.'))
            return

        # 중복 확인
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f'❌ 이메일 "{email}"이(가) 이미 존재합니다.'))
            return

        # 비밀번호 입력
        import getpass
        password = getpass.getpass('비밀번호 (Password): ')
        if not password:
            self.stdout.write(self.style.ERROR('비밀번호는 필수입니다.'))
            return

        password_confirm = getpass.getpass('비밀번호 확인 (Password again): ')
        if password != password_confirm:
            self.stdout.write(self.style.ERROR('❌ 비밀번호가 일치하지 않습니다.'))
            return

        # 회사 ID 입력
        company_id = input('회사 ID (Company ID): ').strip()
        if not company_id:
            self.stdout.write(self.style.ERROR('회사 ID는 필수입니다.'))
            return

        try:
            company = Company.objects.get(company_id=int(company_id))
        except (Company.DoesNotExist, ValueError):
            self.stdout.write(self.style.ERROR(f'❌ 회사 ID "{company_id}"를 찾을 수 없습니다.'))
            return

        # 부서 목록 표시
        self.stdout.write(self.style.WARNING(f'\n{company.name}의 부서:'))
        departments = Department.objects.filter(company=company)
        if departments.exists():
            for d in departments:
                self.stdout.write(f'  ID: {d.department_id} - {d.name}')
        else:
            self.stdout.write('  (부서 없음)')

        # 부서 ID 입력 (선택사항)
        department_id = input('\n부서 ID (선택사항, 엔터로 건너뛰기): ').strip()
        department = None
        if department_id:
            try:
                department = Department.objects.get(department_id=int(department_id), company=company)
            except (Department.DoesNotExist, ValueError):
                self.stdout.write(self.style.WARNING(f'⚠️  부서 ID "{department_id}"를 찾을 수 없습니다. 부서 없이 진행합니다.'))
                department = None

        # 슈퍼 관리자 생성
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                company=company,
                department=department,
            )
            self.stdout.write(self.style.SUCCESS(f'\n✅ 슈퍼 관리자 "{username}" 생성 완료!'))
            self.stdout.write(f'   - 이메일: {email}')
            self.stdout.write(f'   - 회사: {company.name}')
            if department:
                self.stdout.write(f'   - 부서: {department.name}')
            self.stdout.write(f'   - 역할: super_admin')
            self.stdout.write(f'   - 상태: active')
            self.stdout.write('')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ 슈퍼 관리자 생성 실패: {str(e)}'))
