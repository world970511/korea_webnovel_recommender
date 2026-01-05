#!/bin/bash

echo "======================================"
echo "웹소설 추천 시스템 - 초기 설정"
echo "======================================"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Python 가상환경을 생성합니다..."
    python3.10 -m venv venv
    echo "✅ 가상환경 생성 완료"
else
    echo "✅ 가상환경이 이미 존재합니다."
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 pip를 업그레이드합니다..."
pip install --upgrade pip

# Install backend dependencies
echo ""
echo "📦 백엔드 의존성을 설치합니다..."
pip install -r backend/requirements.txt

# Install frontend dependencies
echo ""
echo "📦 프론트엔드 의존성을 설치합니다..."
pip install -r frontend/requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "⚙️  환경 설정 파일을 생성합니다..."
    cp .env.example .env
    echo "✅ .env 파일이 생성되었습니다."
else
    echo "✅ .env 파일이 이미 존재합니다."
fi

# Initialize database
echo ""
echo "🗄️  데이터베이스를 초기화합니다..."
echo "⚠️  이 과정은 임베딩 모델 다운로드로 인해 시간이 걸릴 수 있습니다."
echo ""
read -p "데이터베이스를 초기화하시겠습니까? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd backend
    python init_db.py
    cd ..
    echo ""
fi

echo ""
echo "======================================"
echo "✨ 설치가 완료되었습니다!"
echo "======================================"
echo ""
echo "다음 명령어로 서버를 실행하세요:"
echo ""
echo "  백엔드:    bash run_backend.sh"
echo "  프론트엔드: bash run_frontend.sh"
echo ""
echo "또는 두 개의 터미널에서 각각 실행하세요."
echo "======================================"
