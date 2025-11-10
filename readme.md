# 📚 AI 웹소설 추천 시스템

> 자연어로 원하는 스토리를 설명하면 RAG(Retrieval-Augmented Generation) 기반으로 맞춤 웹소설을 추천하는 AI 시스템


## 🎯 프로젝트 개요

사용자가 140자 이내의 자연어로 원하는 장르, 테마, 스토리를 설명하면, 의미적 유사도 기반 벡터 검색과 LLM을 활용하여 가장 적합한 웹소설을 추천하는 시스템입니다.

### 핵심 특징

- 🔍 **자연어 검색**: "성장형 주인공이 나오는 다크판타지 소설" 같은 자연스러운 문장으로 검색
- 🎯 **의미 기반 매칭**: 단순 키워드가 아닌 문맥의 의미를 이해하여 추천
- 🚀 **FastAPI 백엔드**: 빠르고 안정적인 RESTful API
- 🎨 **Streamlit 프론트엔드**: 직관적이고 사용하기 쉬운 웹 인터페이스
- 🤖 **LangChain 기반**: HuggingFace 또는 Ollama 임베딩 모델 지원
- 💾 **PostgreSQL + PGVector**: 프로덕션 환경에 적합한 벡터 데이터베이스


## 🛠️ 기술 스택

### 백엔드
- **FastAPI**: 고성능 웹 프레임워크
- **LangChain**: LLM 애플리케이션 개발 프레임워크
- **HuggingFace Transformers**: 한국어 임베딩 모델 (`jhgan/ko-sroberta-multitask`)
- **PostgreSQL + PGVector**: 벡터 데이터베이스
- **Pydantic**: 데이터 검증 및 설정 관리

### 프론트엔드
- **Streamlit**: 빠른 웹 앱 개발
- **Requests**: HTTP 클라이언트

### 기타
- **Python 3.11 (권장)**: Python 3.11 또는 3.12 사용 권장 (3.13은 일부 패키지 호환성 문제 가능)
- **Uvicorn**: ASGI 서버

## ⚠️ 중요: Python 버전

**Python 3.11 또는 3.12를 사용하세요.**

Python 3.13은 아직 최신 버전이라 일부 패키지(numpy, psycopg 등)의 pre-built wheel이 없어 컴파일 오류가 발생할 수 있습니다.

```bash
# Python 버전 확인
python --version

# Python 3.11 또는 3.12가 아니라면 해당 버전 설치 필요
```


## 📦 설치 및 실행

### 0. Python 버전 확인 (중요!)

```bash
# Python 버전 확인
python --version

# 또는
python3 --version
```

**Python 3.11 또는 3.12가 아니라면:**
- Windows: [Python 3.11 다운로드](https://www.python.org/downloads/)
- macOS: `brew install python@3.11`
- Linux: `sudo apt install python3.11` 또는 `pyenv`로 버전 관리

### 1. 저장소 클론

```bash
git clone <repository-url>
cd korea_webnovel_recommender
```

### 2. PostgreSQL 설치 및 실행

**Docker 사용 (권장)**
```bash
# Docker Compose로 PostgreSQL + PGVector 실행
docker-compose up -d

# 상태 확인
docker-compose ps
```

**직접 설치**
- PostgreSQL 14 이상 설치
- PGVector 확장 설치
- 데이터베이스 생성: `webnovel_db`

### 3. 자동 설치 (권장)

```bash
bash setup.sh
```

이 스크립트는 다음 작업을 자동으로 수행합니다:
- Python 가상환경 생성
- 필요한 패키지 설치
- 환경 설정 파일 생성
- 데이터베이스 초기화 (선택 사항)

### 3. 수동 설치

```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 백엔드 의존성 설치
pip install -r backend/requirements.txt

# 프론트엔드 의존성 설치
pip install -r frontend/requirements.txt

# 환경 설정 파일 복사
cp .env.example .env

# 데이터베이스 초기화
cd backend
python init_db.py
cd ..
```

### 4. 서버 실행

**백엔드 서버** (터미널 1):
```bash
bash run_backend.sh
```
- 서버 주소: http://localhost:8000
- API 문서: http://localhost:8000/docs

**프론트엔드 서버** (터미널 2):
```bash
bash run_frontend.sh
```
- 앱 주소: http://localhost:8501


## 🎮 사용 방법

1. 웹 브라우저에서 http://localhost:8501 접속
2. 검색창에 원하는 웹소설 스타일 입력
   - 예: "회귀한 주인공이 게임처럼 성장하는 판타지 소설"
   - 예: "현대 배경에서 초능력을 얻은 주인공의 학원물"
3. 검색 버튼 클릭
4. AI가 추천하는 유사한 웹소설 목록 확인


## 📁 프로젝트 구조

```
korea_webnovel_recommender/
├── backend/                # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py        # FastAPI 앱 진입점
│   │   ├── config.py      # 설정 관리
│   │   ├── models.py      # Pydantic 모델
│   │   ├── api/
│   │   │   └── routes.py  # API 라우트
│   │   └── services/
│   │       ├── embedding.py   # 임베딩 서비스
│   │       └── vector_db.py   # PostgreSQL + PGVector 서비스
│   ├── init_db.py         # DB 초기화 스크립트
│   └── requirements.txt
├── frontend/              # Streamlit 프론트엔드
│   ├── app.py            # Streamlit 앱
│   └── requirements.txt
├── data/
│   └── sample_novels.json # 샘플 웹소설 데이터
├── docker-compose.yml     # PostgreSQL + PGVector Docker 설정
├── .env.example          # 환경 변수 템플릿
├── .gitignore
├── setup.sh              # 설치 스크립트
├── run_backend.sh        # 백엔드 실행 스크립트
├── run_frontend.sh       # 프론트엔드 실행 스크립트
└── readme.md
```


## 🔌 API 엔드포인트

### 소설 검색
```
POST /v1/novels/search
```
자연어 쿼리로 유사한 소설 검색

### 소설 상세 정보
```
GET /v1/novels/{novel_id}
```
특정 소설의 상세 정보 조회

### 인기 키워드
```
GET /v1/keywords/popular
```
자주 검색되는 키워드 목록

### 유사 소설 추천
```
GET /v1/novels/{novel_id}/similar
```
특정 소설과 유사한 다른 소설 추천

### 플랫폼별 소설 목록
```
GET /v1/novels?platform={platform}&page={page}&limit={limit}
```
플랫폼별 소설 목록 조회

자세한 API 문서는 http://localhost:8000/docs 에서 확인하세요.


## ⚙️ 환경 설정

`.env` 파일에서 다음 설정을 변경할 수 있습니다:

```env
# 백엔드 설정
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# 임베딩 모델 설정
EMBEDDING_MODEL=jhgan/ko-sroberta-multitask

# PostgreSQL 설정
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=webnovel_db

# API 설정
MAX_QUERY_LENGTH=140
DEFAULT_SEARCH_LIMIT=10
MAX_SEARCH_LIMIT=50
```


## 🎨 커스터마이징

### 새로운 소설 추가

1. `data/sample_novels.json` 파일 수정 또는
2. Admin API 엔드포인트 사용:

```bash
curl -X POST http://localhost:8000/v1/admin/novels \
  -H "Content-Type: application/json" \
  -d '[{
    "title": "소설 제목",
    "author": "작가명",
    "description": "소설 설명",
    "platform": "플랫폼명",
    "url": "https://...",
    "keywords": ["키워드1", "키워드2"]
  }]'
```

### 임베딩 모델 변경

`.env` 파일에서 `EMBEDDING_MODEL` 변경:
- HuggingFace: `jhgan/ko-sroberta-multitask` (기본값)
- 다른 한국어 모델: `sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens`


## 🐛 문제 해결

### Python 3.13 컴파일 오류
**증상**: `pg_config not found`, `Rust required`, `compiler not found` 등의 오류
**해결**: Python 3.11 또는 3.12로 다운그레이드

```bash
# 현재 버전 확인
python --version

# Python 3.11 또는 3.12 설치 후
# 새 가상환경 생성
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 재설치
pip install -r backend/requirements.txt
```

### PostgreSQL 연결 실패
- Docker Compose가 실행 중인지 확인: `docker-compose ps`
- PostgreSQL이 포트 5432에서 실행 중인지 확인
- `.env` 파일의 데이터베이스 설정 확인

### 백엔드 서버 연결 실패
- 백엔드 서버가 실행 중인지 확인: http://localhost:8000/v1/health
- 포트 8000이 이미 사용 중인지 확인
- PostgreSQL 연결 상태 확인

### 임베딩 모델 다운로드 느림
- 첫 실행 시 모델 다운로드로 시간이 걸릴 수 있습니다
- 인터넷 연결 확인

### PGVector 확장 오류
- PostgreSQL에서 PGVector 확장이 활성화되었는지 확인
- Docker Compose 사용 시 자동으로 설치됨


## 📚 참고 자료

- [RAG를 활용한 도서 추천 시스템](https://jchiang1225.medium.com/book-recommendation-with-retrieval-augmented-generation-part-i-d1b415aff558)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [LangChain 공식 문서](https://python.langchain.com/)
- [Streamlit 공식 문서](https://docs.streamlit.io/)
- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [PGVector GitHub](https://github.com/pgvector/pgvector)


## 📝 라이선스

MIT License


## 👥 기여

이슈와 풀 리퀘스트는 언제나 환영합니다!

