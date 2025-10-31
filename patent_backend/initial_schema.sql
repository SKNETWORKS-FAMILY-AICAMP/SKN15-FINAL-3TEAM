--
-- PostgreSQL 초기 스키마 생성 스크립트
-- RDS 또는 새로운 데이터베이스에서 실행
-- 사용법: psql -h <HOST> -U <USER> -d <DATABASE> -f initial_schema.sql
--

-- UUID 확장 활성화 (필수)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ======================================================
-- ENUM 타입 정의
-- ======================================================

-- 사용자 역할
CREATE TYPE user_role AS ENUM ('user', 'dept_admin', 'super_admin');

-- 사용자 상태
CREATE TYPE user_status AS ENUM ('active', 'pending', 'suspended');

-- 관리자 요청 상태
CREATE TYPE admin_request_status AS ENUM ('pending', 'approved', 'rejected');

-- 요청 타입
CREATE TYPE request_type_enum AS ENUM ('user_approval', 'dept_admin', 'password_reset');


-- ======================================================
-- 테이블 생성
-- ======================================================

-- 회사 테이블
CREATE TABLE company (
    company_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    domain VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE company IS '회사 정보';
COMMENT ON COLUMN company.company_id IS '회사 고유 ID';
COMMENT ON COLUMN company.name IS '회사명 (중복 불가)';
COMMENT ON COLUMN company.domain IS '회사 도메인 (예: example.com)';


-- 부서 테이블
CREATE TABLE department (
    department_id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, name),
    FOREIGN KEY (company_id) REFERENCES company(company_id) ON DELETE CASCADE
);

COMMENT ON TABLE department IS '부서 정보';
COMMENT ON COLUMN department.department_id IS '부서 고유 ID';
COMMENT ON COLUMN department.company_id IS '소속 회사 ID';
COMMENT ON COLUMN department.name IS '부서명';


-- 사용자 테이블
CREATE TABLE "user" (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(150) NOT NULL UNIQUE,
    email VARCHAR(254) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    company_id INTEGER NOT NULL,
    department_id INTEGER,
    role user_role NOT NULL DEFAULT 'user',
    status user_status NOT NULL DEFAULT 'pending',
    first_name VARCHAR(150) DEFAULT '',
    last_name VARCHAR(150) DEFAULT '',
    is_staff BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES company(company_id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL,
    CONSTRAINT username_format_check CHECK (username ~ '^[a-zA-Z0-9_]+$')
);

COMMENT ON TABLE "user" IS '사용자 정보';
COMMENT ON COLUMN "user".user_id IS '사용자 고유 ID (UUID)';
COMMENT ON COLUMN "user".username IS '사용자명 (로그인 ID, 중복 불가)';
COMMENT ON COLUMN "user".email IS '이메일 (중복 불가)';
COMMENT ON COLUMN "user".password_hash IS '비밀번호 해시';
COMMENT ON COLUMN "user".role IS '역할: user(일반), dept_admin(부서관리자), super_admin(슈퍼관리자)';
COMMENT ON COLUMN "user".status IS '상태: active(활성), pending(승인대기), suspended(정지)';


-- 관리 요청 테이블 (통합: 회원 승인, 부서 관리자 권한, 비밀번호 초기화)
CREATE TABLE admin_request (
    request_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    target_user_id UUID,
    company_id INTEGER,
    department_id INTEGER,
    request_type request_type_enum DEFAULT 'user_approval',
    status admin_request_status NOT NULL DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    handled_by UUID,
    handled_at TIMESTAMP,
    comment TEXT,
    FOREIGN KEY (user_id) REFERENCES "user"(user_id) ON DELETE CASCADE,
    FOREIGN KEY (target_user_id) REFERENCES "user"(user_id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES company(company_id),
    FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE CASCADE,
    FOREIGN KEY (handled_by) REFERENCES "user"(user_id) ON DELETE SET NULL
);

COMMENT ON TABLE admin_request IS '부서 관리자 권한 승인 요청';
COMMENT ON COLUMN admin_request.request_id IS '요청 고유 ID';
COMMENT ON COLUMN admin_request.user_id IS '요청자 (부서 관리자 후보)';
COMMENT ON COLUMN admin_request.department_id IS '관리할 부서';
COMMENT ON COLUMN admin_request.handled_by IS '처리한 슈퍼 관리자';
COMMENT ON COLUMN admin_request.status IS '상태: pending(대기), approved(승인), rejected(거부)';


-- 검색 히스토리 테이블 (Django managed)
CREATE TABLE search_history (
    history_id UUID PRIMARY KEY,
    query TEXT NOT NULL,
    search_type VARCHAR(50) NOT NULL,
    results_count INTEGER NOT NULL,
    results_summary JSONB,
    created_at TIMESTAMPTZ NOT NULL,
    is_shared BOOLEAN NOT NULL,
    company_id INTEGER NOT NULL,
    created_by_id UUID,
    department_id INTEGER,
    FOREIGN KEY (company_id) REFERENCES company(company_id),
    FOREIGN KEY (created_by_id) REFERENCES "user"(user_id),
    FOREIGN KEY (department_id) REFERENCES department(department_id)
);


-- ======================================================
-- 인덱스 생성
-- ======================================================

-- Company 인덱스
CREATE INDEX idx_company_name ON company(name);
CREATE INDEX idx_company_domain ON company(domain);

-- Department 인덱스
CREATE INDEX idx_department_company_id ON department(company_id);
CREATE INDEX idx_department_name ON department(name);

-- User 인덱스
CREATE INDEX idx_user_username ON "user"(username);
CREATE INDEX idx_user_email ON "user"(email);
CREATE INDEX idx_user_company_id ON "user"(company_id);
CREATE INDEX idx_user_department_id ON "user"(department_id);
CREATE INDEX idx_user_role ON "user"(role);
CREATE INDEX idx_user_status ON "user"(status);

-- AdminRequest 인덱스
CREATE INDEX idx_admin_request_user_id ON admin_request(user_id);
CREATE INDEX idx_admin_request_target_user_id ON admin_request(target_user_id);
CREATE INDEX idx_admin_request_department_id ON admin_request(department_id);
CREATE INDEX idx_admin_request_type ON admin_request(request_type);
CREATE INDEX idx_admin_request_status ON admin_request(status);
CREATE INDEX idx_admin_request_requested_at ON admin_request(requested_at);
CREATE INDEX idx_admin_request_handled_by ON admin_request(handled_by);

-- SearchHistory 인덱스 (Django managed)
CREATE INDEX search_history_company_id_4b46b59e ON search_history(company_id);
CREATE INDEX search_history_created_by_id_4408f97f ON search_history(created_by_id);
CREATE INDEX search_history_department_id_de075875 ON search_history(department_id);
CREATE INDEX search_hist_company_b08412_idx ON search_history(company_id, department_id, created_at DESC);
CREATE INDEX search_hist_created_617a0b_idx ON search_history(created_by_id, created_at DESC);


-- ======================================================
-- 트리거 (updated_at 자동 갱신)
-- ======================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_company_updated_at BEFORE UPDATE ON company
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_department_updated_at BEFORE UPDATE ON department
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_updated_at BEFORE UPDATE ON "user"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- 완료
SELECT 'Schema created successfully!' AS message;
