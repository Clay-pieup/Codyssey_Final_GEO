"""실측: 질의 1회 소요 시간 + 웹 검색 켬/끔 답변 비교.

실행 (프로젝트 맨 위 폴더에서, GEMINI_API_KEY 필요):
    python -m ai.measure

실존 식당 정보를 물어보면 입력합니다. 가게 수만큼 반복할 수 있습니다.
질문 3개 × (웹 검색 끔, 켬) × 2회 = 가게 1곳당 12회 호출, 보통 몇 분 안에 끝납니다.
결과는 화면에 표로 나오고 docs/작업기록/실측결과.md 파일로도 저장됩니다.
"""

import re
import statistics
from datetime import datetime
from pathlib import Path

from ai.gemini_client import ask_gemini

REPEAT = 2  # 질문·모드마다 반복 횟수
RESULT_PATH = Path("docs/작업기록/실측결과.md")


def normalize(text: str) -> str:
    """언급 판정용 표기 통일 (질문세트_측정기준.md 5-1)."""
    text = text.lower().replace("돈가스", "돈까스")
    return re.sub(r"[^0-9a-z가-힣]", "", text)


def store_key(store: str) -> str:
    """지점명 제거 후 비교용 상호. 예: '행복돈까스 망원점' → '행복돈까스'"""
    store = re.sub(r"\s*\S+점$", "", store.strip()) or store
    return normalize(store)


def make_questions(dong: str, menu: str) -> list[str]:
    """실측용 고정 질문 3개 (지역 일반형·메뉴형·조건형 각 1개)."""
    return [
        f"{dong} 맛집 추천해줘",
        f"{dong} {menu} 맛집",
        f"{dong} 가성비 좋은 식당",
    ]


def measure_store(store: str, dong: str, menu: str) -> list[dict]:
    key = store_key(store)
    rows = []
    for q in make_questions(dong, menu):
        for use_search in (False, True):
            for run in range(1, REPEAT + 1):
                r = ask_gemini(q, use_search=use_search)
                mentioned = bool(r.ok and key and key in normalize(r.text))
                rows.append({
                    "store": store, "question": q, "search": use_search, "run": run,
                    "ok": r.ok, "elapsed": r.elapsed, "mentioned": mentioned,
                    "sources": len(r.sources), "length": len(r.text),
                    "preview": r.text[:120].replace("\n", " ") if r.ok else r.error[:120],
                    "model": r.model,
                })
                mode = "켬" if use_search else "끔"
                status = f"{r.elapsed}초" if r.ok else "실패"
                print(f"  [{mode}] {q} ({run}회) → {status}, 언급 {'O' if mentioned else 'X'}, 출처 {len(r.sources)}개")
    return rows


def summarize(rows: list[dict]) -> str:
    lines = []
    model = next((r["model"] for r in rows if r["model"]), "")
    lines.append(f"## 실측 {datetime.now():%m/%d %H:%M} · 모델 {model}\n")

    lines.append("### 1. 질의 1회 소요 시간\n")
    lines.append("| 웹 검색 | 성공/전체 | 평균(초) | 최대(초) | 36회 순차 예상(초) |")
    lines.append("| --- | :-: | :-: | :-: | :-: |")
    for s in (False, True):
        part = [r for r in rows if r["search"] == s]
        ok = [r["elapsed"] for r in part if r["ok"]]
        if ok:
            avg, mx = statistics.mean(ok), max(ok)
            lines.append(f"| {'켬' if s else '끔'} | {len(ok)}/{len(part)} | {avg:.1f} | {mx:.1f} | {avg * 36:.0f} |")
        else:
            lines.append(f"| {'켬' if s else '끔'} | 0/{len(part)} | - | - | - |")
    lines.append("\n- Vercel 실행 1회 제한 300초. 36회 순차 예상이 300초를 넘으면 동시 호출 필요\n")

    lines.append("### 2. 웹 검색 켬/끔 언급 비교\n")
    lines.append("| 가게 | 질문 | 끔: 언급/성공 | 켬: 언급/성공 | 켬: 평균 출처 수 |")
    lines.append("| --- | --- | :-: | :-: | :-: |")
    seen = []
    for r in rows:
        k = (r["store"], r["question"])
        if k in seen:
            continue
        seen.append(k)
        cells = []
        for s in (False, True):
            part = [x for x in rows if (x["store"], x["question"]) == k and x["search"] == s and x["ok"]]
            cells.append(f"{sum(x['mentioned'] for x in part)}/{len(part)}")
        on = [x["sources"] for x in rows if (x["store"], x["question"]) == k and x["search"] and x["ok"]]
        src = f"{statistics.mean(on):.1f}" if on else "-"
        lines.append(f"| {k[0]} | {k[1]} | {cells[0]} | {cells[1]} | {src} |")

    lines.append("\n### 3. 답변 앞부분 (웹 검색 켬, 1회차)\n")
    for r in rows:
        if r["search"] and r["run"] == 1:
            lines.append(f"- **{r['store']} · {r['question']}**: {r['preview']}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    print("실측을 시작합니다. 실존 식당 정보를 입력하세요. (상호를 비우고 Enter → 종료)\n")
    rows = []
    while True:
        store = input("상호 (예: 행복돈까스 망원점): ").strip()
        if not store:
            break
        dong = input("동 이름 (예: 망원동): ").strip()
        menu = input("대표 메뉴 1개 (예: 돈까스): ").strip()
        print(f"\n{store} 측정 중... (호출 {3 * 2 * REPEAT}회)")
        rows += measure_store(store, dong, menu)
        print()

    if not rows:
        print("입력된 가게가 없어 종료합니다.")
        return

    report = summarize(rows)
    print("\n" + report)
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("a", encoding="utf-8") as f:
        f.write(report + "\n")
    print(f"결과를 {RESULT_PATH} 에 저장했습니다.")


if __name__ == "__main__":
    main()