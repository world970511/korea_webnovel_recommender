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
- 💾 **ChromaDB**: 효율적인 벡터 검색


## 🛠️ 기술 스택

### 백엔드
- **FastAPI**: 고성능 웹 프레임워크
- **LangChain**: LLM 애플리케이션 개발 프레임워크
- **HuggingFace Transformers**: 한국어 임베딩 모델 (`jhgan/ko-sroberta-multitask`)
- **ChromaDB**: 벡터 데이터베이스
- **Pydantic**: 데이터 검증 및 설정 관리

### 프론트엔드
- **Streamlit**: 빠른 웹 앱 개발
- **Requests**: HTTP 클라이언트

### 기타
- **Python 3.8+**: 프로그래밍 언어
- **Uvicorn**: ASGI 서버


## 📦 설치 및 실행

### 1. 저장소 클론

```bash
git clone <repository-url>
cd korea_webnovel_recommender
```

### 2. 자동 설치 (권장)

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
│   │       └── vector_db.py   # ChromaDB 서비스
│   ├── init_db.py         # DB 초기화 스크립트
│   └── requirements.txt
├── frontend/              # Streamlit 프론트엔드
│   ├── app.py            # Streamlit 앱
│   └── requirements.txt
├── data/
│   └── sample_novels.json # 샘플 웹소설 데이터
├── chroma_db/            # ChromaDB 저장소 (자동 생성)
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

# ChromaDB 설정
CHROMA_PERSIST_DIRECTORY=./chroma_db

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

### 백엔드 서버 연결 실패
- 백엔드 서버가 실행 중인지 확인: http://localhost:8000/v1/health
- 포트 8000이 이미 사용 중인지 확인

### 임베딩 모델 다운로드 느림
- 첫 실행 시 모델 다운로드로 시간이 걸릴 수 있습니다
- 인터넷 연결 확인

### ChromaDB 오류
- `chroma_db/` 디렉토리 삭제 후 `python backend/init_db.py` 재실행


## 📚 참고 자료

- [RAG를 활용한 도서 추천 시스템](https://jchiang1225.medium.com/book-recommendation-with-retrieval-augmented-generation-part-i-d1b415aff558)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [LangChain 공식 문서](https://python.langchain.com/)
- [Streamlit 공식 문서](https://docs.streamlit.io/)
- [ChromaDB 공식 문서](https://docs.trychroma.com/)


## 📝 라이선스

MIT License


## 👥 기여

이슈와 풀 리퀘스트는 언제나 환영합니다!

