"""상호·지역 표기를 다루는 작은 도구 모음 (docs/기술/질문세트_측정기준.md 1-2, 5-1)."""

import re


def normalize(text: str) -> str:
    """비교용 표기 통일: 소문자, 돈가스→돈까스, 공백·특수문자 제거.

    예: "행복 돈가스!" → "행복돈까스"
    """
    text = text.lower().replace("돈가스", "돈까스")
    return re.sub(r"[^0-9a-z가-힣]", "", text)


def store_key(store: str) -> str:
    """지점명을 뗀 비교용 상호. 예: "행복돈까스 망원점" → "행복돈까스" """
    base = re.sub(r"\s+\S+점$", "", store.strip()) or store
    return normalize(base)


def extract_dong(region: str) -> str:
    """지역 입력에서 손님이 부르는 동 이름을 꺼낸다.

    예: "서울 마포구 망원동" → "망원동"
        "서울 성동구 성수동2가" → "성수동" (1가·2가·3가 제거)
        "부산 연제구 연산1동" → "연산동" (숫자 동 제거)
    동이 없으면 마지막 단어를 그대로 쓴다.
    """
    words = region.strip().split()
    for word in reversed(words):
        if word.endswith("동") or re.search(r"\d가$", word):
            name = re.sub(r"\d+가$", "", word)      # 성수동2가 → 성수동
            name = re.sub(r"\d+동$", "동", name)     # 연산1동 → 연산동
            return name
    return words[-1] if words else ""