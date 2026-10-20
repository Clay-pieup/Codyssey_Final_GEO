"""품질 점검: 같은 입력으로 진단을 3번 돌려 Must 기능이 2번 이상 기대 결과를 내는지 확인한다.

근거: 평가기준 G4 "Must 기능마다 3회 시도 중 2회 이상 기대 결과", docs/AI_활용명세.md 0장
- Must ① 진단 실행: 성공 + 질문 10개 + 언급률 계산됨 + 개선 제안 3개
- Must ② AI Agent 추가 진단: 고른 질문 종류(tool_label)와 이유(why)가 1개 이상 기록됨
  - 언급이 많은 가게는 "더 자세히 진단하기"(run_more)까지 눌러서 확인
- 결과는 화면에 출력하고 docs/작업기록/품질점검.md 맨 아래에 표로 덧붙인다

실행 (프로젝트 맨 위 폴더에서):
    python -m ai.quality_check

무료 키로 돌릴 때는 .env 에 GEMINI_USE_SEARCH=0, GEMINI_REPEAT=1, GEMINI_CONCURRENCY=2 권장
(진단 1번에 약 1~2분, 분당 한도에 걸리면 기다렸다가 다시 시도하므로 더 걸릴 수 있음)
"""

import time
from datetime import datetime
from pathlib import Path

from ai.diagnosis import CONCURRENCY, REPEAT, USE_SEARCH, run_diagnosis, run_more
from ai.gemini_client import current_model

RUNS = 3  # 평가기준 G4: 3회 시도 중 2회 이상
OUT = Path(__file__).resolve().parent.parent / "docs" / "작업기록" / "품질점검.md"

CASES = {
    "1": {"title": "명동교자 (언급 많음 → 버튼으로 Agent 확인)", "store": "명동교자", "region": "서울 중구 명동",
          "station": "", "menus": ["칼국수", "만두"]},
    "2": {"title": "가상 가게 (언급 0% → 자동 Agent 확인)", "store": "행복돈까스 망원점", "region": "서울 마포구 망원동",
          "station": "망원역", "menus": ["등심돈까스", "치즈돈까스"]},
}


def check_must1(rep: dict) -> str:
    """Must ① 기대 결과를 못 맞춘 이유. 맞으면 빈 문자열."""
    if not rep.get("ok"):
        detail = next((str(p) for p in rep.get("problems", []) if p), "")  # 시간 초과·한도 초과 등 원인
        return f"진단 실패: {rep.get('error')}" + (f" ({detail[:60]})" if detail else "")
    if len(rep.get("questions", [])) != 10:
        return "질문이 10개가 아님"
    if rep["summary"]["mention"]["rate"] is None:
        return "언급률 계산 안 됨 (정상 답변 0개)"
    if len(rep.get("suggestions", [])) != 3:
        return f"개선 제안 {len(rep.get('suggestions', []))}개"
    return ""


def check_must2(rep: dict) -> str:
    """Must ② 기대 결과를 못 맞춘 이유. 맞으면 빈 문자열."""
    ag = rep.get("agent") or {}
    if not ag.get("ran"):
        return "Agent 실행 안 됨"
    if ag.get("error"):
        return f"Agent 오류: {ag['error'][:60]}"
    if not any(t.get("tool_label") and t.get("why") for t in ag.get("trace", [])):
        return "고른 도구·이유 기록 없음"
    return ""


def run_case(case: dict) -> list[dict]:
    rows = []
    for i in range(1, RUNS + 1):
        print(f"\n[{i}/{RUNS}회차] 진단 중… ({case['store']})")
        started = time.perf_counter()
        rep = run_diagnosis(case["store"], case["region"], case["menus"], case["station"])
        pressed = False
        if rep.get("ok") and rep.get("more_available"):
            print("  자동 Agent 결과 없음(언급률이 높거나 실패) → '더 자세히 진단하기'(run_more) 실행")
            rep = run_more(rep)
            pressed = True
        m = (rep.get("summary") or {}).get("mention") or {}
        ag = rep.get("agent") or {}
        row = {
            "run": i,
            "ok": rep.get("ok", False),
            "elapsed": round(time.perf_counter() - started, 1),
            "mention": f"{m.get('mentioned', '-')}/{m.get('valid', '-')} ({m.get('rate')}%)" if m else "-",
            "agent": ("버튼" if pressed else ("자동" if ag.get("ran") else "안 함")),
            "tools": ", ".join(t["tool_label"] for t in ag.get("trace", [])) or "-",
            "why": (ag.get("trace") or [{}])[0].get("why", ""),
            "suggestions": len(rep.get("suggestions", [])),
            "warnings": len(rep.get("question_warnings", [])),
            "must1": check_must1(rep),
            "must2": check_must2(rep),
            "model": rep.get("model", ""),
        }
        rows.append(row)
        print(f"  결과: 언급 {row['mention']} / Agent {row['agent']}: {row['tools']} / 제안 {row['suggestions']}개 / {row['elapsed']}초")
        print(f"  Must ①: {'통과' if not row['must1'] else '미달 - ' + row['must1']}")
        print(f"  Must ②: {'통과' if not row['must2'] else '미달 - ' + row['must2']}")
    return rows


def _cell(text) -> str:
    """표 칸에 넣을 글자: | 와 줄바꿈이 표를 깨지 않게 바꾼다."""
    return str(text).replace("|", "/").replace("\n", " ")[:80]


def to_markdown(case: dict, rows: list[dict]) -> str:
    p1 = sum(1 for r in rows if not r["must1"])
    p2 = sum(1 for r in rows if not r["must2"])
    model = next((r["model"] for r in rows if r["model"]), "")
    lines = [
        f"## {datetime.now():%m/%d %H:%M} · {case['store']} ({case['region']}, {', '.join(case['menus'])}"
        + (f", {case['station']}" if case["station"] else "") + ")",
        "",
        f"- 설정: 모델 {model} · 웹 검색 {'켬' if USE_SEARCH else '끔'} · 반복 {REPEAT}회 · 동시 {CONCURRENCY}개",
        f"- **Must ① 진단 실행 {p1}/{RUNS}회 통과 → {'기준 충족' if p1 >= 2 else '기준 미달'}** (기대 결과: 성공, 질문 10개, 언급률 표시, 개선 제안 3개)",
        f"- **Must ② AI Agent 추가 진단 {p2}/{RUNS}회 통과 → {'기준 충족' if p2 >= 2 else '기준 미달'}** (기대 결과: 고른 질문 종류와 이유 표시)",
        "",
        "| 회차 | 언급(정상 답변 중) | Agent | 고른 질문 종류 | 제안 | 질문 경고 | 시간(초) | Must ① | Must ② |",
        "| :-: | :-: | :-: | --- | :-: | :-: | :-: | --- | --- |",
    ]
    for r in rows:
        lines.append(
            f"| {r['run']} | {r['mention']} | {r['agent']} | {r['tools']} | {r['suggestions']} | {r['warnings']} | {r['elapsed']} "
            f"| {'통과' if not r['must1'] else _cell(r['must1'])} | {'통과' if not r['must2'] else _cell(r['must2'])} |"
        )
    lines.append("")
    for r in rows:
        if r["why"]:
            lines.append(f"- {r['run']}회차 AI가 쓴 이유: {_cell(r['why'])}")
    return "\n".join(lines) + "\n\n"


def main() -> None:
    print("품질 점검: 같은 입력으로 진단 3번 (평가기준 G4: 3회 중 2회 이상)\n")
    for k, c in CASES.items():
        print(f"  {k}. {c['title']}")
    print("  3. 직접 입력")
    pick = input("\n번호: ").strip()
    if pick in CASES:
        case = CASES[pick]
    else:
        case = {
            "store": input("상호: ").strip(),
            "region": input("지역 (시·구·동): ").strip(),
            "station": input("가까운 역 (없으면 Enter): ").strip(),
            "menus": [m.strip() for m in input("대표 메뉴 1~3개, 쉼표로 구분: ").split(",") if m.strip()],
        }
    print(f"설정: 모델 {current_model()} / 웹 검색 {'켬' if USE_SEARCH else '끔'} / 반복 {REPEAT}회 / 동시 {CONCURRENCY}개")
    if current_model() == "gemini-3.8-flash" and not USE_SEARCH:
        print("  참고: 3.8-flash는 호출 1번에 17초 정도 걸려 무료 키 점검에는 느립니다. .env 에 GEMINI_MODEL=gemini-3.5-flash-lite 권장")

    rows = run_case(case)
    md = to_markdown(case, rows)
    print("\n" + md)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not OUT.exists():
        OUT.write_text(
            "# AI 품질 점검 기록\n\n"
            "> `python -m ai.quality_check`가 자동으로 덧붙이는 기록입니다. 같은 입력으로 진단을 3번 돌려\n"
            "> Must 기능이 3회 중 2회 이상 기대 결과를 내는지 확인합니다 (평가기준 G4).\n\n",
            encoding="utf-8",
        )
    with OUT.open("a", encoding="utf-8") as f:
        f.write(md)
    print(f"→ {OUT.relative_to(OUT.parent.parent.parent)} 에 덧붙였습니다.")


if __name__ == "__main__":
    main()
