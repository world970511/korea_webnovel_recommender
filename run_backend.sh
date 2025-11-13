#!/bin/bash

echo "======================================"
echo "웹소설 추천 시스템 - 백엔드 서버 시작"
echo "======================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  가상환경이 없습니다. 먼저 설치를 실행해주세요:"
    echo "    bash setup.sh"
    exit 1
fi

# Activate virtual environment
source ./venv/bin/activate

# Run backend
echo "🚀 FastAPI 서버를 시작합니다..."
echo "📍 서버 주소: http://localhost:8000"
echo "📚 API 문서: http://localhost:8000/docs"
echo ""

cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
