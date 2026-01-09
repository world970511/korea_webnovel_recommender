"""
간단한 HTTP 요청으로 카카오페이지 HTML 가져오기
"""
import sys

try:
    import requests
except ImportError:
    print("requests 라이브러리를 설치합니다...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"])
    import requests

url = "https://page.kakao.com/content/68327039"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

try:
    response = requests.get(url, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        html = response.text

        # HTML을 파일로 저장
        with open("kakao_page_initial.html", "w", encoding="utf-8") as f:
            f.write(html)

        print(f"HTML 저장 완료: kakao_page_initial.html")
        print(f"HTML 길이: {len(html)} characters")

        # 주요 요소 검색
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        print("\n" + "="*80)
        print("HTML 구조 분석")
        print("="*80)

        # 제목 찾기
        title_candidates = []
        for tag in ['h1', 'h2', 'h3']:
            titles = soup.find_all(tag)
            for t in titles[:3]:
                title_candidates.append((tag, t.get_text(strip=True)[:50]))

        print("\n제목 후보:")
        for tag, text in title_candidates:
            if text:
                print(f"  <{tag}>: {text}")

        # opacity-70 클래스 찾기
        print("\n\nopacity-70 요소:")
        opacity_elements = soup.select("span.opacity-70")
        for el in opacity_elements[:5]:
            text = el.get_text(strip=True)
            classes = el.get('class', [])
            print(f"  - {text[:50]} (classes: {', '.join(classes)})")

        # whitespace-pre-wrap 찾기
        print("\n\nwhitespace-pre-wrap 요소:")
        wrap_elements = soup.select("span.whitespace-pre-wrap")
        for el in wrap_elements[:3]:
            text = el.get_text(strip=True)
            preview = text[:80] + "..." if len(text) > 80 else text
            classes = el.get('class', [])
            print(f"  - {preview} (classes: {', '.join(classes)})")

        # font-small2-bold 찾기
        print("\n\nfont-small2-bold 요소:")
        bold_elements = soup.select("span.font-small2-bold")
        for el in bold_elements[:10]:
            text = el.get_text(strip=True)
            if text:
                print(f"  - {text}")

        # align-middle 찾기
        print("\n\nalign-middle 요소:")
        align_elements = soup.select("span.align-middle")
        for el in align_elements[:5]:
            text = el.get_text(strip=True)
            classes = el.get('class', [])
            print(f"  - {text} (classes: {', '.join(classes)})")

        # 정보 탭 링크 찾기
        print("\n\n정보 탭 후보:")
        info_tabs = soup.select("a[href*='tab_type']")
        for tab in info_tabs:
            href = tab.get('href', '')
            text = tab.get_text(strip=True)
            print(f"  - {text}: {href}")

    else:
        print(f"Error: HTTP {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
