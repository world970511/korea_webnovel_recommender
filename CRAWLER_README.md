# 웹소설 크롤러 가이드

네이버 시리즈 웹소설을 크롤링하고 데이터베이스에 저장하는 시스템입니다.

## 📁 프로젝트 구조

```
backend/scripts/
├── crawlers/
│   ├── base_crawler.py      # 기본 크롤러 클래스
│   └── naver_crawler.py     # 네이버 시리즈 크롤러
├── processors/
│   └── data_processor.py    # 데이터 전처리 및 검증
├── main_crawler.py          # 메인 실행 스크립트
└── scheduler.py             # 자동화 스케줄러
```

## 🚀 시작하기

### 1. 의존성 설치

```bash
# 가상환경 활성화
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 새로운 패키지 설치
pip install -r backend/requirements.txt
```

### 2. 데이터베이스 확인

PostgreSQL 컨테이너가 실행 중인지 확인:

```bash
podman ps | grep webnovel_postgres
```

실행되지 않았다면:

```bash
podman-compose up -d
```

## 📊 크롤링 실행

### 기본 사용법

#### 테스트 모드 (2페이지만 크롤링)

```bash
./run_crawler.sh --test
```

#### 빠른 크롤링 (기본 정보만, 10페이지)

```bash
./run_crawler.sh 10
```

#### 상세 크롤링 (모든 정보 포함, 느림)

```bash
./run_crawler.sh --details 5
```

#### 전체 크롤링 (모든 페이지)

```bash
./run_crawler.sh
```

### Python으로 직접 실행

```bash
cd backend/scripts

# 테스트
python main_crawler.py --test

# 기본 크롤링
python main_crawler.py --max-pages 10

# 상세 크롤링
python main_crawler.py --details --max-pages 5

# 전체 크롤링
python main_crawler.py

# JSON만 저장 (DB 저장 안함)
python main_crawler.py --no-db

# DB만 저장 (JSON 저장 안함)
python main_crawler.py --no-json
```

## 🤖 자동화 (11/15 이후)

### 스케줄러 실행

매일 자정에 자동으로 크롤링을 실행합니다:

```bash
./run_scheduler.sh
```

스케줄러는 백그라운드에서 계속 실행되며, 다음 실행 시간을 표시합니다.
종료하려면 `Ctrl+C`를 누르세요.

### Systemd로 영구 실행 (Linux)

서버 재부팅 후에도 자동 실행되도록 설정:

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/webnovel-crawler.service
```

내용:

```ini
[Unit]
Description=Web Novel Crawler Scheduler
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/korea_webnovel_recommender
ExecStart=/path/to/korea_webnovel_recommender/run_scheduler.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

서비스 시작:

```bash
sudo systemctl enable webnovel-crawler
sudo systemctl start webnovel-crawler
sudo systemctl status webnovel-crawler
```

## 📋 크롤링 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--platform` | 플랫폼 선택 (naver만 지원) | `--platform naver` |
| `--max-pages` | 최대 페이지 수 | `--max-pages 10` |
| `--details` | 상세 페이지 크롤링 | `--details` |
| `--no-json` | JSON 저장 안함 | `--no-json` |
| `--no-db` | DB 저장 안함 | `--no-db` |
| `--test` | 테스트 모드 (2페이지) | `--test` |

## 📝 데이터 형식

크롤링된 데이터는 다음 형식으로 저장됩니다:

```json
{
  "title": "소설 제목",
  "author": "작가명",
  "description": "줄거리 설명",
  "platform": "네이버시리즈",
  "url": "https://series.naver.com/novel/detail.series?productNo=12345",
  "keywords": ["판타지", "회귀", "성장"]
}
```

### 저장 위치

- **JSON 파일**: `data/naver_novels_YYYYMMDD_HHMMSS.json`
- **로그 파일**: `backend/scripts/crawler_YYYYMMDD_HHMMSS.log`
- **데이터베이스**: PostgreSQL `webnovel_db.novels` 테이블

## 🔧 커스터마이징

### 크롤링 속도 조절

`backend/scripts/crawlers/naver_crawler.py`:

```python
crawler = NaverSeriesCrawler(delay=2.0)  # 2초 대기 (기본 1.5초)
```

### 스케줄 시간 변경

`backend/scripts/scheduler.py`:

```python
trigger = CronTrigger(
    hour=0,      # 자정
    minute=0,
    timezone='Asia/Seoul'
)
```

다른 스케줄 예시:

```python
# 매일 오전 6시
trigger = CronTrigger(hour=6, minute=0, timezone='Asia/Seoul')

# 매주 월요일 자정
trigger = CronTrigger(day_of_week='mon', hour=0, minute=0, timezone='Asia/Seoul')

# 매 3시간마다
trigger = CronTrigger(hour='*/3', timezone='Asia/Seoul')
```

## ⚠️ 주의사항

### 1. Rate Limiting

- 기본 1.5초 딜레이가 설정되어 있습니다
- 너무 빠른 요청은 IP 차단의 원인이 될 수 있습니다
- 대량 크롤링 시 `--details` 옵션은 신중하게 사용하세요

### 2. robots.txt 준수

크롤링 전에 확인:

```bash
curl https://series.naver.com/robots.txt
```

### 3. 법적 고려사항

- 메타데이터(제목, 작가, 설명)만 수집합니다
- 본문 내용은 수집하지 않습니다
- 상업적 사용 시 저작권 확인 필요

### 4. 에러 처리

크롤링 중 에러 발생 시:

1. 로그 파일 확인: `crawler_*.log`
2. 네트워크 연결 확인
3. 사이트 구조 변경 여부 확인
4. HTML 셀렉터 업데이트 필요할 수 있음

## 🐛 트러블슈팅

### "No novels collected" 오류

```bash
# HTML 구조가 변경되었을 가능성
# naver_crawler.py의 셀렉터를 확인하고 업데이트 필요
```

### 데이터베이스 연결 실패

```bash
# PostgreSQL 컨테이너 상태 확인
podman ps -a | grep postgres

# 재시작
podman restart webnovel_postgres
```

### 크롤링이 너무 느림

```bash
# 상세 크롤링 대신 기본 크롤링 사용
./run_crawler.sh 10

# 또는 페이지 수 제한
./run_crawler.sh --details 3
```

## 📈 11/15까지 데이터 수집 계획

### 1단계: 테스트 (11/11)

```bash
./run_crawler.sh --test
```

결과 확인 후 HTML 셀렉터 조정

### 2단계: 점진적 크롤링 (11/11-11/14)

```bash
# 매일 조금씩 크롤링
./run_crawler.sh 50  # 50페이지씩
```

### 3단계: 전체 크롤링 (11/14)

```bash
# 모든 페이지 크롤링
./run_crawler.sh
```

### 4단계: 자동화 시작 (11/15~)

```bash
# 스케줄러 실행
./run_scheduler.sh

# 또는 systemd 서비스로 등록
sudo systemctl enable webnovel-crawler
sudo systemctl start webnovel-crawler
```

## 📊 데이터 확인

### JSON 파일 확인

```bash
cat data/naver_novels_*.json | jq '.[0]'
```

### 데이터베이스 확인

```bash
podman exec webnovel_postgres psql -U postgres -d webnovel_db -c "SELECT COUNT(*) FROM novels;"
podman exec webnovel_postgres psql -U postgres -d webnovel_db -c "SELECT title, author, platform FROM novels LIMIT 5;"
```

## 🔜 향후 확장

### 카카오페이지 크롤러 (동적)

```python
# backend/scripts/crawlers/kakao_crawler.py
from selenium import webdriver
# 무한 스크롤 처리 필요
```

### 리디북스 크롤러 (로그인 필요)

```python
# backend/scripts/crawlers/ridi_crawler.py
# 로그인 세션 관리 필요
```

## 📞 문제 발생 시

1. 로그 파일 확인: `backend/scripts/crawler_*.log`
2. GitHub Issues에 로그와 함께 보고
3. HTML 구조 변경 시 셀렉터 업데이트 필요

## 📚 참고 자료

- [Beautiful Soup 문서](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests 문서](https://requests.readthedocs.io/)
- [APScheduler 문서](https://apscheduler.readthedocs.io/)
