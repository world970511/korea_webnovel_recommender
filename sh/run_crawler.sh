#!/bin/bash
# Web Novel Crawler Runner Script

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}웹소설 크롤러 실행${NC}"
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

# Run crawler
cd backend/scripts || exit 1

echo -e "${GREEN}크롤러 시작...${NC}"
echo ""

# Parse arguments
if [ "$1" == "--test" ]; then
    echo -e "${YELLOW}🧪 테스트 모드 (2페이지만)${NC}"
    python main_crawler.py --test
elif [ "$1" == "--details" ]; then
    echo -e "${YELLOW}📖 상세 정보 포함 크롤링 (느림)${NC}"
    python main_crawler.py --details --max-pages "${2:-10}"
else
    echo -e "${YELLOW}⚡ 빠른 크롤링 (기본 정보만)${NC}"
    python main_crawler.py --max-pages "${1:-10}"
fi

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ 크롤링 완료!${NC}"
else
    echo -e "${RED}❌ 크롤링 실패 (exit code: $exit_code)${NC}"
fi

exit $exit_code
