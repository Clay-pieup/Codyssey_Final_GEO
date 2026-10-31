"""가게 이름으로 네이버 지역 검색 → 화면 자동 입력용 목록으로 정리한다.

근거: docs/ARCHITECTURE.md 5장 (POST /api/places), 진행 기록 10/31 (네이버 지역 검색 결정)
- 네이버 열쇠(Client Secret)는 브라우저에 두면 노출되므로 서버만 네이버를 부른다
- 네이버는 한 번에 최대 5개만 준다 → 화면 안내: "가게 이름 + 동네"로 검색
- 지역은 지번 주소에서 시·구·동까지만 잘라 쓴다 (AI 진단은 "동"이 있는 지역만 받음)
"""

import html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

# 2026년부터 네이버 검색 API는 네이버 클라우드 "NAVER API HUB"로 옮겨감 → 주소·헤더 이름이 예전 개발자센터와 다름
SEARCH_URL = "https://naverapihub.apigw.ntruss.com/search/v1/local"
TIMEOUT_SEC = 5      # 검색은 짧게 기다리고, 실패하면 직접 입력으로 안내
MAX_RESULTS = 5      # 네이버 지역 검색이 한 번에 주는 최대 개수
TAG_PATTERN = re.compile(r"<[^>]+>")  # 검색어 강조용 <b> 태그 제거


def clean_text(text: str) -> str:
    """"<b>명동</b>교자" → "명동교자". &amp; 같은 기호도 원래 글자로 바꾼다."""
    return html.unescape(TAG_PATTERN.sub("", text or "")).strip()


def region_from_address(address: str) -> tuple[str, str]:
    """지번 주소에서 '시·구·동'까지만 잘라 (지역, 안내 문장)을 돌려준다. 안내가 ""이면 그대로 써도 됨.

    "서울특별시 중구 명동2가 25-2" → ("서울특별시 중구 명동2가", "")
    "경기도 양평군 양평읍 ..."      → ("", "읍·면 지역은 아직 지원하지 않아요")
    """
    words = (address or "").split()
    for i, word in enumerate(words):
        if re.search(r"동(\d+가)?$", word):          # 망원동, 명동2가, 성수동1가
            return " ".join(words[: i + 1]), ""
        if word.endswith(("읍", "면", "리")) and i >= 1:
            return "", "읍·면 지역은 아직 지원하지 않아요"
    return "", "지역(동)을 찾지 못했어요. 직접 입력해 주세요"   # 종로2가처럼 이름에 '동'이 없는 곳


# 업종 이름이라 메뉴로 쓰기 어려운 말 (예: "카페,디저트>카페"의 "카페")
BROAD_WORDS = {"한식", "중식", "일식", "양식", "분식", "음식점", "한식당", "중식당", "일식당", "양식당",
               "카페", "디저트", "술집", "요리주점", "아시아음식", "퓨전요리", "뷔페", "패밀리레스토랑"}


def menus_from_category(category: str) -> list[str]:
    """네이버 업종에서 대표 메뉴 후보를 뽑는다 (최대 3개). 사장님이 고칠 수 있는 '후보'일 뿐이다.

    "한식>칼국수,만두" → ["칼국수", "만두"] / "일식>돈가스" → ["돈가스"] / "카페,디저트>카페" → []
    """
    if ">" not in (category or ""):
        return []                                   # "한식"처럼 큰 분류만 있으면 메뉴를 알 수 없음
    words = [w.strip() for w in category.split(">")[-1].split(",")]
    menus = []
    for word in words:
        if word and word not in BROAD_WORDS and word not in menus:
            menus.append(word)
    return menus[:3]


def to_place(item: dict) -> dict:
    """네이버 결과 1개를 화면에 필요한 칸만 남긴 모양으로 바꾼다."""
    address = clean_text(item.get("address", ""))
    region, region_note = region_from_address(address)
    return {
        "name": clean_text(item.get("title", "")),
        "category": clean_text(item.get("category", "")),       # 예: 한식>칼국수,만두
        "address": address,                                     # 지번 주소
        "road_address": clean_text(item.get("roadAddress", "")), # 도로명 주소 (사장님 확인용)
        "region": region,                                        # 자동 입력할 지역 ("" 이면 직접 입력)
        "region_note": region_note,
        "menus": menus_from_category(clean_text(item.get("category", ""))),  # 대표 메뉴 후보 (없으면 [])
    }


def search_places(query: str) -> dict:
    """네이버에 검색하고 {ok, error, places}를 돌려준다. 실패해도 예외 대신 안내 문장을 돌려준다."""
    client_id = os.getenv("NAVER_CLIENT_ID", "").strip()
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return {"ok": False, "error": "가게 검색이 아직 준비되지 않았어요. 직접 입력해 주세요.", "places": []}

    url = SEARCH_URL + "?" + urllib.parse.urlencode({"query": query, "display": MAX_RESULTS, "sort": "random", "format": "json"})
    request = urllib.request.Request(url, headers={
        "X-NCP-APIGW-API-KEY-ID": client_id,      # API HUB 애플리케이션의 Client ID
        "X-NCP-APIGW-API-KEY": client_secret,     # 같은 애플리케이션의 Client Secret
    })
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SEC) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[places] 네이버 응답 {e.code}")            # 열쇠·검색어는 로그에 남기지 않음
        message = "검색이 많아 잠시 멈췄어요. 직접 입력해 주세요." if e.code == 429 else "가게 검색에 실패했어요. 직접 입력해 주세요."
        return {"ok": False, "error": message, "places": []}
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        print(f"[places] 네이버 연결 실패: {type(e).__name__}")
        return {"ok": False, "error": "가게 검색에 실패했어요. 직접 입력해 주세요.", "places": []}

    places = [to_place(item) for item in (data.get("items") or [])[:MAX_RESULTS]]
    return {"ok": True, "error": "" if places else "검색 결과가 없어요. 가게 이름과 동네를 함께 넣어 보세요.", "places": places}
