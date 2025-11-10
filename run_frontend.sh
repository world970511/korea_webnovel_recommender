#!/bin/bash

echo "======================================"
echo "웹소설 추천 시스템 - 프론트엔드 시작"
echo "======================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  가상환경이 없습니다. 먼저 설치를 실행해주세요:"
    echo "    bash setup.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Run frontend
echo "🚀 Streamlit 앱을 시작합니다..."
echo "📍 앱 주소: http://localhost:8501"
echo ""

cd frontend
streamlit run app.py
