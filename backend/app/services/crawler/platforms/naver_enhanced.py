"""
Enhanced Naver Series Crawler with Detail Page Extraction

상세 페이지 방문을 통한 완전한 정보 수집
"""

import asyncio
from typing import List, Dict, Optional
from backend.app.services.crawler.base import BaseCrawler
from backend.app.config import settings


class NaverSeriesCrawlerEnhanced(BaseCrawler):
    """
    향상된 네이버 시리즈 크롤러.

    목록 페이지의 간단한 정보만 수집하는 대신,
    각 소설의 상세 페이지를 방문하여 완전한 정보를 수집합니다.
    """

    BASE_URL = "https://series.naver.com/novel"
    LOGIN_URL = "https://nid.naver.com/nidlogin.login"

    GENRE_MAP = {
        "판타지": "fantasy",
        "현대판타지": "modern_fantasy",
        "로맨스": "romance",
        "로맨스판타지": "romance_fantasy",
        "무협": "martial_arts",
        "BL": "bl",
        "미스터리": "mystery",
        "드라마": "drama",
    }

    def __init__(self, skyvern_client):
        """Initialize enhanced Naver Series crawler."""
        super().__init__(skyvern_client, "naver_series")
        self.is_logged_in = False

    async def crawl_genre_with_details(
        self,
        genre: str,
        limit: int = 20,
        include_adult: bool = False
    ) -> List[Dict]:
        """
        상세 페이지 방문을 포함한 크롤링.

        Args:
            genre: Genre name in Korean
            limit: Maximum number of novels to collect
            include_adult: Whether to include adult content

        Returns:
            List of novel dictionaries with complete information
        """
        if include_adult and not self.is_logged_in:
            if settings.naver_username and settings.naver_password:
                await self.login(settings.naver_username, settings.naver_password)

        genre_code = self.GENRE_MAP.get(genre, "fantasy")
        genre_url = f"{self.BASE_URL}/genre/{genre_code}"

        self.logger.info(f"Starting enhanced crawl of {genre} from {genre_url}")

        # 확장된 스키마 - 상세 페이지에서 수집할 정보 포함
        extraction_schema = {
            "title": "소설 제목",
            "author": "작가 이름",
            "description": "소설 상세 줄거리 (긴 버전)",
            "short_description": "짧은 소개글",
            "url": "소설 상세 페이지 URL",
            "keywords": "장르, 태그, 키워드 (쉼표 구분)",
            "status": "연재 상태 (연재중/완결)",
            "total_episodes": "전체 에피소드 수",
            "rating": "별점 또는 평점",
            "views": "조회수",
            "likes": "좋아요 수",
        }

        # 🔑 핵심: 상세 페이지 방문을 명시한 프롬프트
        prompt = f"""
        네이버 시리즈 {genre} 장르에서 소설 정보를 수집하세요.

        ⭐ 중요: 각 소설마다 상세 페이지에 들어가서 완전한 정보를 수집하세요!

        단계별 작업:

        1. 목록 페이지에서 소설 카드 확인
           - 제목과 작가명 확인
           - 상세 페이지 링크 찾기

        2. 각 소설의 상세 페이지로 이동 (링크 클릭)
           - 완전한 줄거리/시놉시스 수집
           - 연재 상태 (연재중/완결) 확인
           - 전체 에피소드 수 확인
           - 태그와 키워드 모두 수집
           - 평점, 조회수, 좋아요 수 확인

        3. 목록 페이지로 돌아가기 (뒤로가기)

        4. 다음 소설로 이동하여 2-3 반복

        5. {limit}개 수집할 때까지 계속
           - 필요하면 "다음 페이지" 클릭

        수집할 정보:
        - 제목: 정확한 소설 제목
        - 작가: 작가명 또는 필명
        - 상세 줄거리: 상세 페이지의 전체 줄거리 (목록의 짧은 소개글이 아님!)
        - 짧은 소개: 목록에 표시된 짧은 설명
        - URL: 상세 페이지 전체 주소
        - 태그/키워드: #로 시작하는 태그, 장르 분류 등 모두
        - 연재 상태: "연재중" 또는 "완결"
        - 에피소드 수: 총 몇 화인지
        - 평점: 별점 (예: 9.8점)
        - 조회수: 전체 조회수
        - 좋아요: 좋아요 또는 추천 수

        주의사항:
        - 반드시 상세 페이지에 들어가서 정보 수집!
        - 목록의 짧은 정보만으로 넘어가지 말 것
        - 정보가 없으면 빈 문자열로 저장
        - 광고나 배너는 무시
        - 중복 제목 제외
        {'- 19세 이상 콘텐츠 포함' if include_adult else '- 19세 이상 콘텐츠 제외'}
        """

        try:
            # Skyvern 실행 - max_steps를 늘려서 상세 페이지 방문 시간 확보
            result = await self.client.run_task(
                url=genre_url,
                prompt=prompt,
                data_extraction_goal="\n".join([
                    f"{k}: {v}" for k, v in extraction_schema.items()
                ]),
                max_steps=limit * 3  # 각 소설당 3 스텝 (목록→상세→복귀)
            )

            # 결과 처리
            raw_novels = result.get("extracted_data", [])

            novels = []
            for raw_novel in raw_novels[:limit]:
                try:
                    normalized = self.normalize_novel_data_enhanced(raw_novel)
                    if genre not in normalized["keywords"]:
                        normalized["keywords"].append(genre)
                    novels.append(normalized)
                except Exception as e:
                    self.logger.warning(f"Failed to normalize novel: {str(e)}")
                    continue

            self.log_crawl_summary(novels)
            return novels

        except Exception as e:
            self.logger.error(f"Failed to crawl {genre}: {str(e)}")
            return []

    def normalize_novel_data_enhanced(self, raw_data: Dict) -> Dict:
        """
        확장된 필드를 포함한 데이터 정규화.

        Args:
            raw_data: Raw data from Skyvern with enhanced fields

        Returns:
            Normalized novel dictionary with additional metadata
        """
        # 기본 필드
        base_novel = {
            "title": raw_data.get("title", "").strip(),
            "author": raw_data.get("author", "").strip(),
            "description": raw_data.get("description", "").strip(),
            "platform": self.platform_name,
            "url": raw_data.get("url", "").strip(),
            "keywords": self._extract_keywords(raw_data),
        }

        # 추가 메타데이터
        metadata = {
            "short_description": raw_data.get("short_description", "").strip(),
            "status": raw_data.get("status", "").strip(),
            "total_episodes": self._parse_number(raw_data.get("total_episodes")),
            "rating": self._parse_float(raw_data.get("rating")),
            "views": self._parse_number(raw_data.get("views")),
            "likes": self._parse_number(raw_data.get("likes")),
        }

        # 연재 상태를 키워드에 추가
        if metadata["status"]:
            base_novel["keywords"].append(metadata["status"])

        # 메타데이터를 설명에 추가 (검색 품질 향상)
        if metadata["status"] or metadata["total_episodes"]:
            extra_info = []
            if metadata["status"]:
                extra_info.append(f"[{metadata['status']}]")
            if metadata["total_episodes"]:
                extra_info.append(f"[총 {metadata['total_episodes']}화]")

            base_novel["description"] += " " + " ".join(extra_info)

        return base_novel

    def _parse_number(self, value) -> Optional[int]:
        """Extract number from string."""
        if not value:
            return None

        import re
        # "1,234회" → 1234
        numbers = re.findall(r'\d+', str(value).replace(",", ""))
        return int(numbers[0]) if numbers else None

    def _parse_float(self, value) -> Optional[float]:
        """Extract float from string."""
        if not value:
            return None

        import re
        # "9.8점" → 9.8
        match = re.search(r'(\d+\.?\d*)', str(value))
        return float(match.group(1)) if match else None

    async def crawl_genre(
        self,
        genre: str,
        limit: int = 20,
        include_adult: bool = False
    ) -> List[Dict]:
        """
        기본 크롤링 메서드 - 상세 페이지 방문 버전으로 리다이렉트.
        """
        return await self.crawl_genre_with_details(genre, limit, include_adult)

    async def login(self, username: str, password: str) -> bool:
        """Login to Naver."""
        try:
            self.logger.info(f"Attempting Naver login for {username}")

            success = await self.client.login_to_site(
                url=self.LOGIN_URL,
                username=username,
                password=password,
                username_field_desc="아이디 입력란",
                password_field_desc="비밀번호 입력란",
                login_button_desc="로그인 버튼"
            )

            self.is_logged_in = success
            return success

        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False
