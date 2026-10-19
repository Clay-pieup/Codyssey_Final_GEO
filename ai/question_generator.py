"""진단 1단계: 가게 정보로 손님 질문 10개를 만든다.

근거: docs/질문세트_측정기준.md 2·3장
- 문장은 AI(Gemini)가 만들고, 개수·상호 미포함·지역 포함 같은 규칙은 이 코드가 검사한다.
- 검사에 실패하면 1회 다시 만들고, 그래도 실패하면 오류를 돌려준다.

혼자 실행해 보기 (프로젝트 맨 위 폴더에서):
    python -m ai.question_generator
"""

import json
from dataclasses import dataclass, field

from ai.gemini_client import ask_gemini
from ai.prompt_loader import load_prompt
from ai.text_utils import extract_dong, normalize, store_key

# 유형별 개수 (측정기준 3장)
TYPE_COUNTS = {"지역 일반형": 2, "메뉴형": 3, "상황형": 3, "조건형": 2}
TOTAL = sum(TYPE_COUNTS.values())  # 10

# 상황·조건 후보 (측정기준 3-1, 3-2). AI가 메뉴에 맞는 것을 고른다.
SITUATIONS = ["혼밥·1인 식사", "데이트", "회식·단체", "가족 외식", "아이와 함께", "친구 모임", "늦은 밤"]
CONDITIONS = ["주차", "예약 가능", "포장", "웨이팅 없는", "분위기 좋은", "오래된 노포"]  # "가성비"는 프롬프트에서 항상 포함

TEMPERATURE = 0.7  # 자연스러운 문장이 필요해서 약간의 다양성 허용 [실측 후 조정]
MAX_ATTEMPTS = 2   # 첫 시도 + 재생성 1회


@dataclass
class QuestionSet:
    ok: bool
    questions: list = field(default_factory=list)  # [{"id": "q1", "type": "...", "text": "..."}]
    dong: str = ""
    attempts: int = 0
    problems: list = field(default_factory=list)   # 마지막 시도에서 걸린 검사 항목
    error: str = ""


def check_questions(questions, store: str, dong: str, station: str = "") -> list[str]:
    """생성된 질문이 규칙을 지키는지 검사하고, 어긴 항목을 문장 목록으로 돌려준다 (빈 목록 = 통과)."""
    problems = []
    if not isinstance(questions, list) or len(questions) != TOTAL:
        return [f"질문 개수가 {TOTAL}개가 아님 ({len(questions) if isinstance(questions, list) else '형식 오류'})"]

    texts = [str(q.get("text", "")).strip() for q in questions]
    types = [q.get("type", "") for q in questions]

    for t, n in TYPE_COUNTS.items():
        if types.count(t) != n:
            problems.append(f"{t} 개수가 {n}개가 아님 ({types.count(t)}개)")

    # 상호가 들어가면 안 됨: 지점명을 뗀 상호 전체, 그리고 상호 앞 4글자(예: "부산할매")
    key = store_key(store)
    head = key[:4] if len(key) >= 4 else key
    for i, text in enumerate(texts, 1):
        n = normalize(text)
        if key and key in n:
            problems.append(f"q{i}에 상호가 들어감: {text}")
        elif head and len(head) >= 3 and head in n:
            problems.append(f"q{i}에 상호 일부가 들어감: {text}")

    # 모든 질문에 지역(동 또는 역) 포함
    station_name = station.strip()
    for i, text in enumerate(texts, 1):
        has_dong = dong and dong in text
        has_station = station_name and (station_name in text or station_name.removesuffix("역") in text)
        if not (has_dong or has_station):
            problems.append(f"q{i}에 지역이 없음: {text}")

    # 역을 입력했으면 동 이름은 6개 이상 (기획서 2-2)
    if station_name:
        dong_count = sum(1 for t in texts if dong in t)
        if dong_count < 6:
            problems.append(f"동 이름이 들어간 질문이 6개 미만 ({dong_count}개)")

    if len(set(texts)) != len(texts):
        problems.append("같은 질문이 중복됨")

    return problems


def generate_questions(store: str, region: str, menus: list[str], station: str = "") -> QuestionSet:
    """가게 정보로 질문 10개를 만든다. 실패하면 ok=False와 이유를 돌려준다."""
    dong = extract_dong(region)
    prompt = load_prompt(
        "question_generation",
        dong=dong,
        station=station.strip() or "없음",
        menus=", ".join(m.strip() for m in menus if m.strip()),
        situations=", ".join(SITUATIONS),
        conditions=", ".join(CONDITIONS),
    )

    problems, error = [], ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        result = ask_gemini(prompt, temperature=TEMPERATURE, json_output=True)
        if not result.ok:
            error = result.error
            continue
        try:
            questions = json.loads(result.text)["questions"]
        except (json.JSONDecodeError, KeyError, TypeError):
            problems = ["JSON 형식 오류"]
            continue
        problems = check_questions(questions, store, dong, station)
        if not problems:
            return QuestionSet(ok=True, questions=questions, dong=dong, attempts=attempt)

    return QuestionSet(
        ok=False, dong=dong, attempts=MAX_ATTEMPTS, problems=problems,
        error=error or "규칙 검사를 통과하지 못함",
    )


def main() -> None:오후 1:31 2026-10-19
    print("질문 생성 테스트 (실존·가상 가게 모두 가능)\n")
    store = input("상호 (예: 행복돈까스 망원점): ").strip()
    region = input("지역 (예: 서울 마포구 망원동): ").strip()
    station = input("가까운 역 (없으면 Enter): ").strip()
    menus = input("대표 메뉴 1~3개, 쉼표로 구분 (예: 등심돈까스, 치즈돈까스): ").split(",")

    qs = generate_questions(store, region, menus, station)
    print(f"\n동 이름: {qs.dong} / 시도 {qs.attempts}회 / {'성공' if qs.ok else '실패'}\n")
    if qs.ok:
        for q in qs.questions:
            print(f"  {q['id']:>3} [{q['type']}] {q['text']}")
    else:
        print(f"  이유: {qs.error}")
        for p in qs.problems:
            print(f"  - {p}")


if __name__ == "__main__":
    main()