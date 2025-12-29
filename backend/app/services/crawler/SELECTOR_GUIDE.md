# 크롤러 Selector 가이드

전통적인 크롤러는 **CSS Selector**와 **XPath** 두 가지 방식을 모두 지원합니다.

## CSS Selector vs XPath

| 특징 | CSS Selector | XPath |
|------|-------------|-------|
| 난이도 | 쉬움 | 중간 |
| 속도 | 빠름 | 중간 |
| 표현력 | 제한적 | 강력함 |
| 부모 탐색 | 불가능 | 가능 |
| 텍스트 조건 | 제한적 | 가능 |
| 형제 탐색 | 제한적 | 가능 |

## CSS Selector 사용법

### 기본 형식

```python
SELECTORS = {
    "list": {
        "item": ".novel-card",           # 클래스로 선택
        "title": "h3.title",             # 태그 + 클래스
        "author": "span.author",
        "url": "a@href",                 # @ 뒤에 속성명
    },
    "detail": {
        "description": ".synopsis p",     # 하위 요소
        "keywords": ".tag[multiple]",     # [multiple] 붙이면 리스트로 반환
        "genre": "#genre-label",          # ID로 선택
    }
}
```

### 주요 CSS Selector 패턴

```python
# 클래스 선택
".class-name"

# ID 선택
"#element-id"

# 태그 선택
"div"

# 속성 선택
"[data-type='novel']"

# 자식 선택
"div > span"

# 하위 선택
"div span"

# 복합 선택
"div.card > h3.title"

# 속성 추출
"a@href"
"img@src"
"div@data-id"

# 여러 개 추출
".tag[multiple]"
"span.keyword[multiple]"
```

## XPath 사용법

### 기본 형식

XPath를 사용하려면 `xpath:` 접두사를 붙입니다.

```python
SELECTORS = {
    "list": {
        "item": "xpath://div[@class='novel-card']",
        "title": "xpath:.//h3[@class='title']",
        "author": "xpath:.//span[contains(@class, 'author')]",
        "url": "xpath:.//a/@href",
    },
    "detail": {
        "description": "xpath:.//div[@class='synopsis']/p",
        "keywords": "xpath:.//span[@class='tag'][multiple]",
        "genre": "xpath:.//div[@id='genre-label']",
    }
}
```

### 주요 XPath 패턴

```python
# 절대 경로 (전체 문서에서)
"xpath://div[@class='container']"

# 상대 경로 (현재 요소 하위에서, list item 내부 검색 시 사용)
"xpath:.//span[@class='author']"

# 속성 조건
"xpath://div[@class='novel']"
"xpath://div[@data-type='webnovel']"

# 텍스트 조건
"xpath://span[text()='판타지']"
"xpath://div[contains(text(), '신작')]"

# 클래스 부분 매칭
"xpath://div[contains(@class, 'novel')]"

# 부모 요소 선택
"xpath://span[@class='title']/.."
"xpath://span[@class='title']/parent::div"

# 형제 요소
"xpath://h3[@class='title']/following-sibling::span"
"xpath://h3[@class='title']/preceding-sibling::div"

# 속성 값 추출
"xpath:.//a/@href"
"xpath:.//img/@src"
"xpath:.//div/@data-id"

# n번째 요소
"xpath:(//div[@class='novel'])[1]"  # 첫 번째
"xpath:(//div[@class='novel'])[last()]"  # 마지막

# 조건 조합
"xpath://div[@class='novel' and @data-status='complete']"
"xpath://div[@class='novel' or @class='webtoon']"

# 여러 개 추출
"xpath:.//span[@class='tag'][multiple]"
"xpath:.//li[multiple]"
```

### XPath 고급 기능

```python
# 텍스트가 특정 값인 요소의 부모 찾기
"xpath://span[text()='작가명']/parent::div"

# 특정 텍스트를 포함하는 요소
"xpath://div[contains(text(), '검색어')]"

# 여러 조건
"xpath://div[@class='novel' and contains(@data-genre, '판타지')]"

# 위치 기반
"xpath://div[@class='list']/div[position() <= 10]"  # 처음 10개

# 텍스트 정규화
"xpath://span[normalize-space(text())='제목']"
```

## 실제 사용 예시

### 예시 1: 네이버 시리즈 (CSS Selector)

```python
SELECTORS = {
    "list": {
        "item": "li.content_item",
        "title": "strong.title",
        "author": "span.author",
        "url": "a.item_link@href",
    },
    "detail": {
        "description": "div.synopsis p",
        "keywords": "span.tag[multiple]",
    }
}
```

### 예시 2: 카카오 페이지 (XPath)

```python
SELECTORS = {
    "list": {
        "item": "xpath://div[@class='list-item']",
        "title": "xpath:.//h3[contains(@class, 'title')]",
        "url": "xpath:.//a[@class='link']/@href",
    },
    "detail": {
        "author": "xpath:.//span[@class='author']",
        "description": "xpath:.//div[@class='description']",
        "keywords": "xpath:.//span[contains(@class, 'tag')][multiple]",
    }
}
```

### 예시 3: 복잡한 구조 (XPath가 유리)

```python
# 시나리오: "작가" 레이블 옆에 있는 실제 작가 이름을 추출
# HTML: <div><span>작가</span><span>홍길동</span></div>

# XPath로 쉽게 가능
"xpath://span[text()='작가']/following-sibling::span"

# CSS로는 불가능 (구조 변경 필요)
```

## 디버깅 팁

### 1. 브라우저 개발자 도구 사용

**CSS Selector 테스트:**
```javascript
// 브라우저 콘솔에서
document.querySelectorAll('.novel-card')
```

**XPath 테스트:**
```javascript
// 브라우저 콘솔에서
$x("//div[@class='novel-card']")
```

### 2. Python에서 테스트

```python
from bs4 import BeautifulSoup
from lxml import html

# HTML 로드
html_content = """<your html here>"""
soup = BeautifulSoup(html_content, 'html.parser')

# CSS Selector 테스트
items = soup.select('.novel-card')
print(f"Found {len(items)} items")

# XPath 테스트
tree = html.fromstring(html_content)
items = tree.xpath("//div[@class='novel-card']")
print(f"Found {len(items)} items")
```

### 3. 크롤러에서 로그 확인

```python
# 로그 레벨을 DEBUG로 설정
import logging
logging.basicConfig(level=logging.DEBUG)

# 크롤러 실행 시 "Found X items on page" 로그 확인
```

## 어느 것을 사용할까?

### CSS Selector를 사용하는 경우:
- ✅ 간단한 구조 (클래스, ID로 선택 가능)
- ✅ 빠른 속도가 중요한 경우
- ✅ 개발자가 CSS에 익숙한 경우

### XPath를 사용하는 경우:
- ✅ 복잡한 조건 (텍스트 기반, 부모/형제 탐색)
- ✅ 위치 기반 선택이 필요한 경우
- ✅ 속성 조합이 복잡한 경우

### 혼용도 가능!

```python
SELECTORS = {
    "list": {
        "item": ".novel-card",  # CSS (간단)
        "title": "xpath:.//h3[contains(@class, 'title')][1]",  # XPath (복잡)
        "url": "a@href",  # CSS (간단)
    }
}
```

## 트러블슈팅

### 문제: 요소를 찾을 수 없음
- 페이지가 완전히 로딩되지 않았을 수 있음 → `wait_time` 증가
- 동적으로 생성되는 요소일 수 있음 → JavaScript 실행 대기
- Selector가 잘못되었을 수 있음 → 브라우저 개발자 도구로 확인

### 문제: 빈 값이 반환됨
- 상대 경로 문제 → XPath에서 `.//` 사용 확인
- 속성명 오타 → `@href` vs `@src` 확인
- 네임스페이스 문제 → 일반적으로 HTML에서는 문제없음

### 문제: 여러 개 추출이 안 됨
- `[multiple]` 추가 확인
- XPath에서 올바른 경로 확인

## 추가 자료

- [CSS Selector 레퍼런스](https://www.w3schools.com/cssref/css_selectors.asp)
- [XPath 치트시트](https://devhints.io/xpath)
- [BeautifulSoup 문서](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [lxml XPath 문서](https://lxml.de/xpathxslt.html)
