"""
카카오페이지 상세 페이지 HTML 구조 확인 스크립트
"""
import asyncio
import sys
import os
from playwright.async_api import async_playwright

async def debug_kakao_page():
    """카카오페이지 상세 페이지의 HTML 구조를 확인"""

    # 카카오페이지 웹소설 상세 페이지 URL (예시)
    # 실제 URL은 목록 페이지에서 하나를 선택하거나 직접 입력
    detail_url = "https://page.kakao.com/content/61259304"

    print(f"\n{'='*80}")
    print(f"카카오페이지 HTML 구조 분석 시작")
    print(f"URL: {detail_url}")
    print(f"{'='*80}\n")

    async with async_playwright() as p:
        # 브라우저 실행 (headless=True - 서버 환경)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            # 1. 상세 페이지 이동
            print("1. 상세 페이지로 이동 중...")
            await page.goto(detail_url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            # 2. 초기 페이지 HTML 저장
            html_before = await page.content()
            with open("kakao_page_before_tab.html", "w", encoding="utf-8") as f:
                f.write(html_before)
            print("   ✓ 초기 HTML 저장: kakao_page_before_tab.html")

            # 3. 정보 탭 찾기 및 클릭
            print("\n2. 정보 탭 찾는 중...")
            tab_selectors = [
                "a[href*='tab_type=about']",
                "button:has-text('정보')",
                "a:has-text('정보')",
                "[role='tab']:has-text('정보')"
            ]

            tab_clicked = False
            for selector in tab_selectors:
                try:
                    tab = await page.query_selector(selector)
                    if tab and await tab.is_visible():
                        print(f"   ✓ 정보 탭 발견: {selector}")
                        await tab.click()
                        print("   ✓ 정보 탭 클릭 완료")
                        tab_clicked = True
                        break
                except Exception as e:
                    continue

            if not tab_clicked:
                print("   ⚠ 정보 탭을 찾을 수 없습니다. 기본 페이지를 분석합니다.")
            else:
                # 탭 클릭 후 대기
                await asyncio.sleep(2)
                await page.wait_for_load_state("networkidle", timeout=10000)

            # 4. 정보 탭 클릭 후 HTML 저장
            html_after = await page.content()
            with open("kakao_page_after_tab.html", "w", encoding="utf-8") as f:
                f.write(html_after)
            print("   ✓ 정보 탭 클릭 후 HTML 저장: kakao_page_after_tab.html")

            # 5. 주요 요소 찾기 시도
            print("\n3. 주요 요소 찾기 시도...\n")

            # Author 후보 셀렉터들
            author_selectors = [
                "span.opacity-70.break-word-anywhere.line-clamp-2",
                "span.opacity-70",
                "span[class*='author']",
                "div[class*='author']",
            ]

            print("   [작가 정보]")
            for selector in author_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        for i, el in enumerate(elements[:3]):  # 최대 3개만
                            text = await el.text_content()
                            classes = await el.get_attribute("class")
                            print(f"   - {selector}: '{text.strip()}' (class: {classes})")
                except:
                    pass

            # Description 후보 셀렉터들
            description_selectors = [
                "span.font-small1.whitespace-pre-wrap.break-words",
                "span.whitespace-pre-wrap",
                "div[class*='description']",
                "p[class*='description']",
            ]

            print("\n   [줄거리 정보]")
            for selector in description_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        for i, el in enumerate(elements[:2]):
                            text = await el.text_content()
                            classes = await el.get_attribute("class")
                            preview = text.strip()[:50] + "..." if len(text.strip()) > 50 else text.strip()
                            print(f"   - {selector}: '{preview}' (class: {classes})")
                except:
                    pass

            # Keywords 후보 셀렉터들
            keyword_selectors = [
                "span.font-small2-bold",
                "span[class*='keyword']",
                "a[class*='tag']",
                "span:has-text('#')",
            ]

            print("\n   [키워드 정보]")
            for selector in keyword_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        keywords = []
                        for el in elements[:10]:
                            text = await el.text_content()
                            if text.strip():
                                keywords.append(text.strip())
                        if keywords:
                            print(f"   - {selector}: {keywords}")
                except:
                    pass

            # Genre 후보 셀렉터들
            genre_selectors = [
                "span.break-all.align-middle",
                "span[class*='genre']",
                "div[class*='category']",
            ]

            print("\n   [장르 정보]")
            for selector in genre_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        for i, el in enumerate(elements[:5]):
                            text = await el.text_content()
                            classes = await el.get_attribute("class")
                            print(f"   - {selector}: '{text.strip()}' (class: {classes})")
                except:
                    pass

            print(f"\n{'='*80}")
            print("분석 완료!")
            print("저장된 파일:")
            print("  - kakao_page_before_tab.html (정보 탭 클릭 전)")
            print("  - kakao_page_after_tab.html (정보 탭 클릭 후)")
            print(f"{'='*80}\n")

        except Exception as e:
            print(f"\n❌ 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(debug_kakao_page())
