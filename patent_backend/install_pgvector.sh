#!/bin/bash
# pgvector 확장 설치 스크립트

echo "🔧 pgvector 확장 설치 중..."

# PostgreSQL에 vector 확장 설치
PGPASSWORD=1q2w3e4r psql -h localhost -U final_play -d patentdb -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>&1 | grep -v "permission denied" || \
sudo -u postgres psql -d patentdb -c "CREATE EXTENSION IF NOT EXISTS vector;"

if [ $? -eq 0 ]; then
    echo "✅ pgvector 확장 설치 완료!"
else
    echo "❌ pgvector 확장 설치 실패. 수동으로 설치해주세요:"
    echo "sudo -u postgres psql -d patentdb -c \"CREATE EXTENSION IF NOT EXISTS vector;\""
fi
