# 📚 AI 웹소설 추천 시스템

> 자연어로 원하는 스토리를 설명하면 RAG(Retrieval-Augmented Generation) 기반으로 맞춤 웹소설을 추천하는 AI 시스템


## 🎯 프로젝트 개요

사용자가 140자 이내의 자연어로 원하는 장르, 테마, 스토리를 설명하면, 의미적 유사도 기반 벡터 검색과 LLM을 활용하여 가장 적합한 웹소설을 추천하는 시스템입니다.

### 핵심 특징
- 🔍 **자연어 검색**: "성장형 주인공이 나오는 다크판타지 소설" 같은 자연스러운 문장으로 검색
- 🎯 **의미 기반 매칭**: 단순 키워드가 아닌 문맥의 의미를 이해하여 추천


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

**Docker/podman 사용 (권장)**
```bash
# Docker Compose로 PostgreSQL + PGVector 실행
docker-compose up -d

# 상태 확인
docker-compose ps
```

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

### 임베딩 모델 변경

`.env` 파일에서 `EMBEDDING_MODEL` 변경:
- HuggingFace: `jhgan/ko-sroberta-multitask` (기본값)
- 다른 한국어 모델: `sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens`


## 📚 참고 자료

- [RAG를 활용한 도서 추천 시스템](https://jchiang1225.medium.com/book-recommendation-with-retrieval-augmented-generation-part-i-d1b415aff558)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [LangChain 공식 문서](https://python.langchain.com/)
- [Streamlit 공식 문서](https://docs.streamlit.io/)
- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [PGVector GitHub](https://github.com/pgvector/pgvector)


## 📝 과정 기록
1) https://world970511.github.io/blog/posts/2025-11-27-korea-webnovel-recommender-1.html
2) https://world970511.github.io/blog/posts/2027-11-27-korea-webnovel-recommender-2.html


