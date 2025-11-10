"""
Streamlit Frontend for Web Novel Recommendation System
"""
import streamlit as st
import requests
from typing import List, Dict, Any
import pandas as pd

# Configuration
API_BASE_URL = "http://localhost:8000/v1"

# Page config
st.set_page_config(
    page_title="웹소설 추천 시스템",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    .novel-card {
        padding: 1.5rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
        border-left: 5px solid #1f77b4;
    }
    .similarity-score {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 5px;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
    }
    .keyword-tag {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem;
        border-radius: 15px;
        background-color: #e1e4e8;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


def search_novels(query: str, limit: int = 10) -> Dict[str, Any]:
    """Search for novels using the API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/novels/search",
            json={"query": query, "limit": limit},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ 백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return None
    except requests.exceptions.Timeout:
        st.error("⚠️ 요청 시간이 초과되었습니다. 다시 시도해주세요.")
        return None
    except Exception as e:
        st.error(f"⚠️ 검색 중 오류가 발생했습니다: {str(e)}")
        return None


def get_popular_keywords(limit: int = 20) -> List[Dict[str, Any]]:
    """Get popular keywords from API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/keywords/popular",
            params={"limit": limit},
            timeout=10
        )
        response.raise_for_status()
        return response.json()["data"]["keywords"]
    except Exception as e:
        st.warning(f"인기 키워드를 불러올 수 없습니다: {str(e)}")
        return []


def get_health_status() -> Dict[str, Any]:
    """Check API health status"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {"status": "unhealthy", "novels_count": 0}


def display_novel_card(novel: Dict[str, Any]):
    """Display a novel card with details"""
    with st.container():
        st.markdown(f"""
        <div class="novel-card">
            <h3>📖 {novel['title']}</h3>
            <p><strong>작가:</strong> {novel['author']}</p>
            <p><strong>플랫폼:</strong> {novel['platform']}</p>
            <p><strong>줄거리:</strong> {novel['description']}</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 3])

        with col1:
            similarity = novel.get('similarity_score', 0)
            st.markdown(f"""
                <div class="similarity-score">
                    유사도: {similarity:.1%}
                </div>
            """, unsafe_allow_html=True)

        with col2:
            keywords_html = "".join([
                f'<span class="keyword-tag">#{kw}</span>'
                for kw in novel.get('keywords', [])
            ])
            st.markdown(keywords_html, unsafe_allow_html=True)

        if novel.get('url'):
            st.markdown(f"[🔗 작품 보러가기]({novel['url']})")

        st.markdown("---")


def main():
    """Main application"""

    # Header
    st.markdown('<h1 class="main-header">📚 AI 웹소설 추천 시스템</h1>', unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; font-size: 1.2rem; color: #666;'>"
        "원하는 스토리를 자연어로 설명하면 딱 맞는 웹소설을 추천해드립니다!"
        "</p>",
        unsafe_allow_html=True
    )

    # Sidebar
    with st.sidebar:
        st.header("⚙️ 설정")

        # Health check
        health = get_health_status()
        if health["status"] == "healthy":
            st.success(f"✅ 서버 정상 (소설 {health.get('novels_count', 0)}편)")
        else:
            st.error("❌ 서버 연결 실패")

        st.markdown("---")

        # Search settings
        st.subheader("검색 설정")
        search_limit = st.slider(
            "검색 결과 개수",
            min_value=1,
            max_value=20,
            value=10,
            help="한 번에 표시할 검색 결과 개수"
        )

        st.markdown("---")

        # Popular keywords
        st.subheader("🔥 인기 키워드")
        popular_keywords = get_popular_keywords(10)
        if popular_keywords:
            for kw in popular_keywords[:10]:
                st.markdown(f"- **{kw['keyword']}** ({kw['count']})")

        st.markdown("---")
        st.markdown(
            "<small>Made with ❤️ using FastAPI + Streamlit</small>",
            unsafe_allow_html=True
        )

    # Main search area
    st.markdown("### 🔍 원하는 웹소설을 설명해주세요")

    # Search examples
    with st.expander("💡 검색 예시 보기"):
        st.markdown("""
        - "주인공이 회귀해서 복수하는 판타지 소설"
        - "게임 세계에 빙의한 주인공이 성장하는 이야기"
        - "현대 배경에서 초능력을 얻은 주인공의 학원물"
        - "던전을 탐험하는 헌터 스토리"
        - "전생해서 마법사가 되는 로맨스 판타지"
        """)

    # Search input
    query = st.text_area(
        "검색어를 입력하세요 (최대 140자)",
        placeholder="예: 회귀한 주인공이 게임처럼 성장하는 판타지 소설",
        max_chars=140,
        height=100
    )

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        search_button = st.button("🔍 검색하기", use_container_width=True, type="primary")

    # Perform search
    if search_button and query:
        with st.spinner("🔎 완벽한 웹소설을 찾고 있습니다..."):
            results = search_novels(query, search_limit)

        if results and results.get("status") == "success":
            data = results["data"]
            st.success(f"✨ {data['total_results']}개의 추천 결과를 찾았습니다!")

            st.markdown("---")
            st.markdown("### 📚 추천 웹소설")

            if data["results"]:
                for idx, novel in enumerate(data["results"], 1):
                    st.markdown(f"#### {idx}. 추천 작품")
                    display_novel_card(novel)
            else:
                st.info("검색 결과가 없습니다. 다른 키워드로 시도해보세요!")

    elif search_button and not query:
        st.warning("⚠️ 검색어를 입력해주세요!")

    # Statistics section
    if not search_button:
        st.markdown("---")
        st.markdown("### 📊 시스템 통계")

        col1, col2, col3 = st.columns(3)

        health = get_health_status()

        with col1:
            st.metric(
                label="등록된 소설",
                value=f"{health.get('novels_count', 0):,}편"
            )

        with col2:
            st.metric(
                label="지원 플랫폼",
                value="5개"
            )

        with col3:
            st.metric(
                label="검색 방식",
                value="AI 기반"
            )


if __name__ == "__main__":
    main()
