# 🕷️ Skyvern 크롤러 설정 가이드

Skyvern + Ollama를 사용한 웹소설 크롤링 시스템 설정 및 사용 가이드

## 📋 목차

1. [개요](#개요)
2. [시스템 요구사항](#시스템-요구사항)
3. [설치 및 설정](#설치-및-설정)
4. [사용 방법](#사용-방법)
5. [플랫폼별 특징](#플랫폼별-특징)
6. [문제 해결](#문제-해결)

---

## 개요

이 크롤러는 **Skyvern**과 **Ollama**를 결합하여 한국 웹소설 플랫폼에서 자동으로 소설 정보를 수집합니다.

### 주요 특징

- ✅ **LLM 기반 크롤링**: 비전 언어 모델이 웹사이트를 이해하고 상호작용
- ✅ **로컬 실행**: Ollama로 비용 없이 로컬에서 실행
- ✅ **다양한 UI 패턴 지원**:
  - 네이버 시리즈: 페이지네이션 + 상세 페이지 진입
  - 카카오페이지: 무한 스크롤 + 상세 페이지 진입
  - 리디북스: 장르별 네비게이션 + 상세 페이지 진입
- ✅ **상세 정보 수집**: 목록 페이지의 요약 정보가 아닌, 각 소설의 상세 페이지를 방문하여 전체 줄거리와 키워드 수집
- ✅ **강건성**: HTML 구조 변경에도 유연하게 대응

### 지원 플랫폼

| 플랫폼 | URL | UI 패턴 | 상태 |
|--------|-----|---------|------|
| 네이버 시리즈 | series.naver.com | 페이지네이션 | ✅ |
| 카카오페이지 | page.kakao.com | 무한 스크롤 | ✅ |
| 리디북스 | ridibooks.com | 장르 네비게이션 | ✅ |

---

## 시스템 요구사항

### 필수 요구사항

- **Python 3.11+** (3.12 권장, 3.13은 호환성 문제 가능)
- **Ollama** (로컬 LLM 실행)
- **4GB+ RAM** (Ollama 모델 실행용)
- **10GB+ 디스크 공간** (모델 저장용)

### 권장 사양

- **8GB+ RAM**: 더 큰 모델 사용 가능
- **GPU**: 추론 속도 향상 (선택사항)

---

## 설치 및 설정

### 1. Ollama 설치

#### Linux / macOS
```bash
# Ollama 설치
curl -fsSL https://ollama.com/install.sh | sh

# 서비스 시작 확인
ollama --version
```

#### Windows
[Ollama 공식 웹사이트](https://ollama.com/download)에서 설치 프로그램 다운로드

### 2. Ollama 모델 다운로드

```bash
# Skyvern 권장 모델 다운로드 (약 4.7GB)
ollama pull qwen2.5:7b-instruct

# 모델 확인
ollama list
```

**대안 모델** (더 작거나 큰 모델):
```bash
# 더 작은 모델 (3GB)
ollama pull qwen2.5:3b-instruct

# 더 큰 모델 (11GB, 더 정확함)
ollama pull qwen2.5:14b-instruct
```

### 3. Skyvern 설치

```bash
# 가상환경 활성화
source venv/bin/activate  # Windows: venv\Scripts\activate

# Skyvern 및 의존성 설치
pip install skyvern playwright

# Playwright 브라우저 설치
playwright install chromium
```

### 4. 환경 설정

`.env` 파일 편집:

```bash
# Skyvern 활성화
ENABLE_SKYVERN=true
ENABLE_OLLAMA=true
OLLAMA_SERVER_URL=http://localhost:11434
SKYVERN_OLLAMA_MODEL=qwen2.5:7b-instruct

# 크롤러 설정
CRAWLER_ENABLED=true
CRAWLER_BATCH_SIZE=20
CRAWLER_DELAY_SECONDS=2

# (선택) 성인 콘텐츠 접근을 위한 로그인 정보
NAVER_USERNAME=your_naver_id
NAVER_PASSWORD=your_password

KAKAO_USERNAME=your_kakao_email
KAKAO_PASSWORD=your_password

RIDI_USERNAME=your_ridi_email
RIDI_PASSWORD=your_password
```

### 5. Ollama 서버 실행 확인

```bash
# Ollama가 실행 중인지 확인
curl http://localhost:11434/api/version

# 또는 브라우저에서
# http://localhost:11434
```

---

## 사용 방법

### 기본 사용법

```bash
# 네이버 시리즈 전체 목록에서 20개 수집 (상세 페이지 방문)
python backend/crawl_novels.py --platform naver --limit 20
# 네이버 시리즈가 가진 전체 데이터를 수집할 경우
python backend/crawl_novels.py --platform naver 

# 카카오페이지 전체 목록에서 30개 수집
python backend/crawl_novels.py --platform kakao --limit 30
# 카카오페이지가 가진 전체 데이터를 수집할 경우
python backend/crawl_novels.py --platform kakao 

# 리디북스에서 판타지소설 50개 수집 (로맨스/로맨스판타지/판타지/BL 장르 지정 가능)
python backend/crawl_novels.py --platform ridi --genres 판타지 --limit 50
# 리디북스가 가진 전체 데이터를 수집할 경우(장르지정x)
python backend/crawl_novels.py --platform ridi 
```


### 신작 수집
```bash
# 카카오페이지 신작
python backend/crawl_novels.py --platform kakao --special new --limit 20

# 리디북스 판타지 신작
python backend/crawl_novels.py --platform ridi --genres 판타지 --special new --limit 20

# 네이버 시리즈 신작
python backend/crawl_novels.py --platform naver --special new --limit 20
```

### 성인 콘텐츠 포함

```bash
# 성인 콘텐츠 포함 수집 (로그인 필요)
python backend/crawl_novels.py --platform naver --genres "BL,로맨스" --limit 20 --adult
```

### 데이터베이스 저장 없이 테스트

```bash
# 결과만 출력하고 DB에 저장하지 않음
python backend/crawl_novels.py --platform naver --genres 판타지 --limit 10 --no-save
```

---

## 고급 사용법

### Python 코드에서 직접 사용

```python
import asyncio
from backend.app.services.crawler.skyvern_client import SkyvernClient
from backend.app.services.crawler.platforms.naver import NaverSeriesCrawlerEnhanced

async def main():
    # Skyvern 클라이언트 초기화
    client = SkyvernClient()

    # 네이버 크롤러 생성 (Enhanced 버전)
    crawler = NaverSeriesCrawlerEnhanced(client)

    # 전체 목록 크롤링 (상세 페이지 방문 포함)
    novels = await crawler.crawl_all_novels(
        limit=20,
        include_adult=False
    )

    # 결과 출력
    for novel in novels:
        print(f"{novel['title']} - {novel['author']}")
        print(f"Description: {novel['description'][:100]}...")

asyncio.run(main())
```

### 커스텀 크롤링 로직

```python
from backend.app.services.crawler.platforms.kakao import KakaoPageCrawler
from backend.app.services.crawler.utils import save_crawled_novels

async def crawl_kakao_new_releases():
    client = SkyvernClient()
    crawler = KakaoPageCrawler(client)

    # 신작 수집
    novels = await crawler.crawl_new_releases(
        limit=30,
        include_adult=False
    )

    # 데이터베이스 저장
    await save_crawled_novels(novels)

    return novels
```

---

## 문제 해결

### Ollama 연결 실패

**증상**: `Connection refused` 또는 `Ollama server not available`

**해결**:
```bash
# Ollama 서비스 재시작
# Linux/macOS
systemctl restart ollama

# 또는 직접 실행
ollama serve

# 포트 확인
netstat -tulpn | grep 11434
```

### 모델 다운로드 느림

**증상**: `ollama pull` 명령이 매우 느림

**해결**:
- 인터넷 연결 확인
- VPN 사용 시 비활성화
- 더 작은 모델 사용: `qwen2.5:3b-instruct`

### Playwright 브라우저 오류

**증상**: `Executable doesn't exist` 또는 `Browser not found`

**해결**:
```bash
# Playwright 브라우저 재설치
playwright install chromium

# 시스템 의존성 설치 (Linux)
playwright install-deps
```

### Skyvern 작업 실패

**증상**: 크롤링 중 `Task failed` 또는 `Extraction failed`

**원인 및 해결**:

1. **웹사이트 구조 변경**
   - 일시적 문제일 수 있음, 재시도
   - 플랫폼이 대규모 업데이트한 경우, 이슈 리포트

2. **Ollama 모델 성능 부족**
   - 더 큰 모델 사용: `qwen2.5:14b-instruct`
   - `.env`에서 `SKYVERN_OLLAMA_MODEL` 변경

3. **네트워크 타임아웃**
   - `.env`에서 `CRAWLER_DELAY_SECONDS` 증가
   - max_steps 파라미터 증가

### 성인 콘텐츠 로그인 실패

**증상**: `Login failed` 또는 인증 오류

**해결**:
1. `.env`에 올바른 계정 정보 확인
2. 2FA 비활성화 (또는 앱 비밀번호 사용)
3. 수동으로 한 번 로그인 후 쿠키 저장 기능 활용

### 메모리 부족 오류

**증상**: `Out of memory` 또는 시스템 느림

**해결**:
```bash
# 더 작은 배치 크기 사용
# .env 파일
CRAWLER_BATCH_SIZE=10

# 더 작은 Ollama 모델 사용
ollama pull qwen2.5:3b-instruct
```

---

## 성능 최적화

### 크롤링 속도 조절

```bash
# .env 설정
CRAWLER_DELAY_SECONDS=1  # 빠르게 (주의: IP 차단 위험)
CRAWLER_DELAY_SECONDS=5  # 안전하게
```

### 병렬 크롤링

```python
import asyncio

async def parallel_crawl():
    tasks = [
        crawl_platform("naver", ["판타지"], 20),
        crawl_platform("kakao", ["로맨스"], 20),
        crawl_platform("ridi", ["무협"], 20),
    ]
    results = await asyncio.gather(*tasks)
    return results
```

### 모델 최적화

| 모델 | 크기 | 속도 | 정확도 | 용도 |
|------|------|------|--------|------|
| qwen2.5:3b-instruct | 3GB | 빠름 | 중간 | 테스트 |
| qwen2.5:7b-instruct | 4.7GB | 중간 | 높음 | 일반 사용 (권장) |
| qwen2.5:14b-instruct | 11GB | 느림 | 매우 높음 | 정확도 중요 시 |

---

## 크롤링 윤리 및 법적 고려사항

⚠️ **주의사항**:

1. **robots.txt 준수**: 각 플랫폼의 크롤링 정책 확인
2. **요청 빈도 제한**: `CRAWLER_DELAY_SECONDS` 설정으로 서버 부하 최소화
3. **저작권**: 수집한 데이터의 사용 목적과 범위 고려
4. **개인정보**: 사용자 리뷰나 댓글 등 개인정보 수집 지양
5. **상업적 이용**: 각 플랫폼의 이용약관 확인

---

## 추가 리소스

- [Skyvern 공식 문서](https://docs.skyvern.com)
- [Ollama 공식 문서](https://ollama.com/docs)
- [Playwright 문서](https://playwright.dev/python/)

---

## 라이선스

MIT License

---

## 기여 및 문의

이슈나 개선사항은 GitHub Issue로 제보해 주세요.
