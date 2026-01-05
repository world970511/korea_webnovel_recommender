#!/bin/bash
# Web Novel Crawler Scheduler Runner Script

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}웹소설 크롤러 스케줄러 시작${NC}"
echo -e "${GREEN}================================${NC}"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}가상환경 활성화 중...${NC}"
    source venv/bin/activate || source venv/Scripts/activate 2>/dev/null
else
    echo -e "${RED}❌ 가상환경을 찾을 수 없습니다${NC}"
    echo -e "${YELLOW}setup.sh를 먼저 실행해주세요${NC}"
    exit 1
fi

# Check if PostgreSQL is running
echo -e "${YELLOW}PostgreSQL 연결 확인 중...${NC}"
if ! podman ps | grep -q webnovel_postgres; then
    echo -e "${RED}❌ PostgreSQL 컨테이너가 실행되지 않았습니다${NC}"
    echo -e "${YELLOW}podman-compose up -d로 실행해주세요${NC}"
    exit 1
fi

# Run scheduler
cd backend/scripts || exit 1

echo -e "${GREEN}스케줄러 시작...${NC}"
echo -e "${YELLOW}매일 자정에 자동으로 크롤링을 실행합니다${NC}"
echo -e "${YELLOW}종료하려면 Ctrl+C를 누르세요${NC}"
echo ""

python scheduler.py

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ 스케줄러 정상 종료${NC}"
else
    echo -e "${RED}❌ 스케줄러 오류 발생 (exit code: $exit_code)${NC}"
fi

exit $exit_code
