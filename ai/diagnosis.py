"""진단 전체 흐름: 입력 확인 → 질문 생성 → 질의 → 답변 분석 → 집계 → Agent 추가 질의 → 개선 제안 → 리포트.

서버(팀장)가 부르는 함수 2개. 결과는 둘 다 JSON으로 바꿀 수 있는 dict(리포트).
- run_diagnosis(): 진단 1회. 언급률 30% 미만이면 Agent 추가 질의까지 자동 실행
- run_more(report): "더 자세히 진단하기" 버튼. 1차 리포트를 그대로 받아 Agent 추가 질의만 실행
  (Vercel은 요청마다 새로 시작해 1차 결과를 기억하지 못하므로 화면이 리포트를 다시 보냄)
근거: 기획서 3장, docs/질문세트_측정기준.md 4~8장

혼자 실행해 보기 (프로젝트 맨 위 폴더에서):
    python -m ai.diagnosis

.env 로 바꿀 수 있는 값
- GEMINI_USE_SEARCH : 웹 검색 사용 (기본 1). 무료 키는 웹 검색 할당량이 없어 로컬 테스트 때는 0
- GEMINI_REPEAT     : 질문마다 반복 횟수 (기본 3). 무료 키 테스트 때는 1로 줄이면 호출이 1/3
- GEMINI_CONCURRENCY: 동시에 보낼 호출 수 (기본 3). 유료 키는 늘려도 됨
"""

import json
import os
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from ai.agent import run_agent
from ai.gemini_client import ask_gemini, current_model
from ai.prompt_loader import load_prompt
from ai.question_generator import TYPE_COUNTS, generate_questions
from ai.text_utils import extract_dong, normalize, store_key

USE_SEARCH = os.getenv("GEMINI_USE_SEARCH", "1") not in ("0", "false", "False", "")
REPEAT = int(os.getenv("GEMINI_REPEAT", "3"))
CONCURRENCY = int(os.getenv("GEMINI_CONCURRENCY", "3"))

NOTICE = "AI가 생성한 추정치입니다. 실제 ChatGPT·Gemini 앱에서 손님이 받는 답변과 다를 수 있습니다."

# "정보를 찾을 수 없다"류 답변 → 정상 답변에서 제외 (측정기준 5-2)
REFUSAL_PATTERNS = ["찾을 수 없", "정보가 없", "알 수 없", "확인할 수 없", "답변하기 어렵", "제공할 수 없"]


# ---------------------------------------------------------------- 1. 입력 확인

def check_input(store: str, region: str, menus: list[str], station: str = "") -> list[str]:
    """AI를 부르기 전에 입력을 확인한다. 문제가 있으면 사장님께 보여줄 문장 목록을 돌려준다."""
    problems = []
    s = store.strip()
    if not s:
        problems.append("상호를 입력해 주세요.")
    elif len(s) > 30:
        problems.append("상호는 30자 이내로 입력해 주세요.")
    elif not re.search(r"[가-힣A-Za-z]", s) or re.fullmatch(r"[ㄱ-ㅎㅏ-ㅣ]+", s.replace(" ", "")):
        problems.append("상호를 다시 확인해 주세요.")

    words = region.strip().split()
    if not any(w.endswith("동") or re.search(r"\d가$", w) for w in words):
        problems.append("지역은 동 이름까지 입력해 주세요. (예: 서울 마포구 망원동)")

    clean_menus = [m.strip() for m in menus if m.strip()]
    if not clean_menus:
        problems.append("대표 메뉴를 1개 이상 입력해 주세요.")
    elif len(clean_menus) > 3:
        problems.append("대표 메뉴는 3개까지 입력해 주세요.")

    if station.strip() and len(station.strip()) > 20:
        problems.append("가까운 역 이름을 다시 확인해 주세요.")
    return problems


# ---------------------------------------------------------------- 2. 질의

def _classify(result) -> str:
    if not result.ok:
        return "failed"
    text = result.text.strip()
    if not text:
        return "empty"
    if len(text) < 80 and any(p in text for p in REFUSAL_PATTERNS):
        return "refused"
    return "ok"


def run_queries(questions: list[dict]) -> list[dict]:
    """질문마다 REPEAT회씩 Gemini에 묻는다. CONCURRENCY개씩 동시에 보내 시간을 줄인다."""
    jobs = [(q, run) for q in questions for run in range(1, REPEAT + 1)]

    def ask(job):
        q, run = job
        r = ask_gemini(q["text"], use_search=USE_SEARCH)  # 손님 질문 그대로, temperature는 모델 기본값
        return {
            "question_id": q["id"], "type": q["type"], "question": q["text"], "run": run,
            "status": _classify(r), "text": r.text, "sources": r.sources,
            "elapsed": r.elapsed, "error": r.error[:200],
        }

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        return list(pool.map(ask, jobs))


# ---------------------------------------------------------------- 3. 답변 분석

def analyze_question(store: str, dong: str, question: str, answers: list[dict]) -> None:
    """같은 질문의 정상 답변들을 한 번에 분석해 각 answer dict에 결과를 채운다 (호출 1회)."""
    key = store_key(store)
    valid = [a for a in answers if a["status"] == "ok"]
    for a in answers:  # 기본값: 코드 판정만
        a["mention_check"] = {"code": bool(key and key in normalize(a["text"])), "ai": None}
        a["mentioned"] = a["mention_check"]["code"] if a["status"] == "ok" else None
        a.update({"rank": None, "description": None, "sentiment": None, "other_stores": []})
    if not valid:
        return

    blocks = "\n\n".join(f"[답변 {i}]\n{a['text'][:3000]}" for i, a in enumerate(valid, 1))
    prompt = load_prompt("answer_analysis", store_name=store, dong=dong, question=question, answers=blocks)
    r = ask_gemini(prompt, temperature=0, json_output=True)
    try:
        results = {int(x["no"]): x for x in json.loads(r.text)["results"]} if r.ok else {}
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        results = {}

    for i, a in enumerate(valid, 1):
        x = results.get(i)
        if not x:
            continue  # 분석 실패 → 코드 판정 결과만 사용
        ai = bool(x.get("mentioned"))
        a["mention_check"]["ai"] = ai
        a["mention_check"]["mismatch"] = ai != a["mention_check"]["code"]
        a["mentioned"] = ai  # 최종값은 AI 판정 (측정기준 5-1)
        if ai:
            a["rank"] = x.get("rank") if x.get("is_list") else None
            a["description"] = x.get("description")
            a["sentiment"] = x.get("sentiment")
        a["other_stores"] = [s for s in (x.get("other_stores") or []) if isinstance(s, dict) and s.get("name")][:5]


def analyze_all(store: str, dong: str, answers: list[dict]) -> None:
    by_q = {}
    for a in answers:
        by_q.setdefault(a["question_id"], []).append(a)
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        list(pool.map(lambda item: analyze_question(store, dong, item[1][0]["question"], item[1]), by_q.items()))


# ---------------------------------------------------------------- 4. 집계

def _rate(part: list[dict]) -> dict:
    valid = [a for a in part if a["status"] == "ok"]
    hit = sum(1 for a in valid if a["mentioned"])
    return {"mentioned": hit, "valid": len(valid), "total": len(part),
            "rate": int(hit / len(valid) * 100) if valid else None}  # 소수점 버림 (측정기준 5-2)


def _source_kind(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if any(k in host for k in ("blog", "tistory", "brunch", "velog")):
        return "블로그"
    if any(k in host for k in ("map", "place", "diningcode", "siksin", "mangoplate", "catchtable", "kakao")):
        return "지도·리뷰"
    if any(k in host for k in ("news", "chosun", "joongang", "donga", "hani", "yna", "mk.co", "hankyung")):
        return "언론"
    return "기타"


def summarize(store: str, answers: list[dict]) -> dict:
    stats = _rate(answers)
    by_type = {t: _rate([a for a in answers if a["type"] == t]) for t in TYPE_COUNTS}

    hits = [a for a in answers if a["status"] == "ok" and a["mentioned"]]
    ranks = [a["rank"] for a in hits if isinstance(a["rank"], int)]
    descriptions = Counter(a["description"] for a in hits if a["description"]).most_common(3)
    sentiments = Counter(a["sentiment"] for a in hits if a["sentiment"])

    key = store_key(store)
    comp_count, comp_desc, comp_menu = Counter(), {}, Counter()
    for a in answers:
        seen = set()
        for s in a["other_stores"]:
            k = normalize(s["name"])
            if not k or k == key or k in seen:
                continue
            seen.add(k)
            comp_count[k] += 1
            comp_desc.setdefault(k, {"name": s["name"], "description": s.get("description") or ""})
            if a["type"] == "메뉴형":
                comp_menu[k] += 1
    menu_valid = by_type["메뉴형"]["valid"]
    competitors = [
        {**comp_desc[k], "answers": n, "menu_answers": f"{comp_menu[k]}/{menu_valid}"}
        for k, n in comp_count.most_common(3)
    ]

    urls = [u for a in answers for u in a["sources"]]
    source_kinds = dict(Counter(_source_kind(u) for u in urls))

    return {
        "mention": stats,
        "by_type": by_type,
        "rank": {"average": round(sum(ranks) / len(ranks), 1) if ranks else None,
                 "first_place": ranks.count(1), "counted": len(ranks)},
        "descriptions": [{"text": t, "count": n} for t, n in descriptions],
        "sentiment": dict(sentiments),
        "competitors": competitors,
        "sources": {"total": len(urls), "kinds": source_kinds},
    }


# ---------------------------------------------------------------- 5. 개선 제안

def suggest(store: str, dong: str, menus: list[str], summary: dict, agent: dict | None = None) -> list[dict]:
    brief = {k: summary.get(k) for k in ("mention", "by_type", "rank", "descriptions", "competitors", "sources")}
    if agent and agent.get("trace"):  # Agent 추가 질의에서 알게 된 것도 근거로 넘김
        brief["agent_findings"] = [
            {"질문 종류": t["tool_label"], "질문": t["question"], "고른 이유": t["why"],
             "결과": f"{t['result']['mentioned']}/{t['result']['valid']} 언급",
             "AI가 소개한 말": t["result"]["descriptions"], "함께 나온 가게": t["result"]["other_stores"]}
            for t in agent["trace"]
        ]
    prompt = load_prompt(
        "improvement", store_name=store, dong=dong, menus=", ".join(menus),
        summary=json.dumps(brief, ensure_ascii=False, indent=1),
    )
    for _ in range(2):
        r = ask_gemini(prompt, temperature=0.3, json_output=True)
        try:
            items = json.loads(r.text)["suggestions"] if r.ok else []
            items = [s for s in items if isinstance(s, dict) and s.get("title")]
            if len(items) >= 3:
                return items[:3]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    return []


# ---------------------------------------------------------------- 6. 진입 함수

def run_diagnosis(store: str, region: str, menus: list[str], station: str = "") -> dict:
    """서버가 부르는 진단 진입 함수. 결과는 JSON으로 바꿀 수 있는 dict.

    ok=False면 error(사장님께 보여줄 문장)와 problems를 보고 화면에 안내하면 된다.
    """
    started = time.perf_counter()
    menus = [m.strip() for m in menus if m and m.strip()]
    report = {
        "ok": False, "error": "", "problems": [],
        "input": {"store": store.strip(), "region": region.strip(), "dong": extract_dong(region),
                  "station": station.strip(), "menus": menus},
        "notice": NOTICE,
        "settings": {"use_search": USE_SEARCH, "repeat": REPEAT, "concurrency": CONCURRENCY},
        "questions": [], "summary": None, "answers": [],
        "agent": {"ran": False, "trigger": "", "reason_to_run": "", "trace": [], "skipped": [], "model": "", "error": ""},
        "more_available": False,  # true면 화면에 "더 자세히 진단하기" 버튼 표시
        "suggestions": [], "model": current_model(), "elapsed_sec": 0,
    }

    problems = check_input(store, region, menus, station)
    if problems:
        report.update(error="입력을 확인해 주세요.", problems=problems)
        return report

    qs = generate_questions(store, region, menus, station)
    if not qs.ok:
        report.update(error="질문을 만들지 못했어요. 잠시 후 다시 시도해 주세요.", problems=qs.problems)
        return _finish(report, started)
    report["questions"] = qs.questions
    report["question_warnings"] = qs.warnings  # 질문 품질 경고 (예: 동 이름 6개 미만), 진단은 계속함

    answers = run_queries(qs.questions)
    if not any(a["status"] == "ok" for a in answers):
        first_error = next((a["error"] for a in answers if a["error"]), "")
        report.update(error="AI 답변을 받지 못했어요. 잠시 후 다시 시도해 주세요.", problems=[first_error])
        report["answers"] = answers
        return _finish(report, started)

    analyze_all(store, qs.dong, answers)
    summary = summarize(store, answers)
    summary["low_reliability"] = summary["mention"]["valid"] < len(answers) * 2 / 3  # 측정기준 4장: 정상 답변 2/3 미만
    report.update(summary=summary, answers=answers)

    report["agent"] = run_agent(store, qs.dong, station.strip(), menus, summary, run_queries, analyze_question)
    report["more_available"] = not report["agent"]["ran"]  # 자동 추가 질의를 안 한 리포트에만 버튼 (기획서 3-1)

    report["suggestions"] = suggest(store, qs.dong, menus, summary, report["agent"])
    report["ok"] = True
    return _finish(report, started)


def _finish(report: dict, started: float) -> dict:
    report["elapsed_sec"] = round(time.perf_counter() - started, 1)
    report["model"] = current_model()  # 실제 모델 이름 (예: gemini-3.5-flash-lite)
    return report


# ---------------------------------------------------------------- 7. "더 자세히 진단하기" 버튼

def run_more(report: dict) -> dict:
    """1차 리포트를 받아 Agent 추가 질의만 실행하고, agent·suggestions를 채운 리포트를 돌려준다.

    - 화면이 run_diagnosis()에서 받은 리포트를 그대로 다시 보내면 됨 (서버는 1차 결과를 기억하지 않음)
    - 언급률과 관계없이 실행. 추가 질의는 진단 1회당 1번 → 이미 추가 질의를 한 리포트면 실행하지 않음
    - 실패해도 1차 결과는 그대로 두고 more_error에 사장님께 보여줄 문장을 넣어 돌려줌
    - 호출 수: 도구 선택 1 + 추가 질의 최대 6 + 추가 분석 최대 2 + 개선 제안 1 = 최대 10회
    """
    started = time.perf_counter()
    if not isinstance(report, dict):
        return {"ok": False, "error": "진단 결과 형식이 올바르지 않아요.", "problems": [], "more_error": "진단 결과 형식이 올바르지 않아요."}
    new = dict(report)  # 받은 리포트는 건드리지 않고 복사본을 고쳐서 돌려줌
    new["more_error"] = ""

    def fail(message: str) -> dict:
        new["more_error"] = message
        return new

    if not report.get("ok"):
        return fail("먼저 진단을 끝까지 실행해 주세요.")
    if (report.get("agent") or {}).get("trace"):
        new["more_available"] = False
        return fail("이미 추가 진단을 했어요. 다시 보려면 새로 진단해 주세요.")

    inp = report.get("input") or {}
    store = str(inp.get("store", ""))
    region = str(inp.get("region", ""))
    station = str(inp.get("station", "") or "")
    menus = [str(m) for m in (inp.get("menus") or []) if str(m).strip()]
    summary = report.get("summary")
    if check_input(store, region, menus, station) or not _summary_ok(summary):
        return fail("진단 결과가 올바르지 않아요. 새로 진단해 주세요.")

    dong = extract_dong(region)
    agent = run_agent(store, dong, station.strip(), menus, summary, run_queries, analyze_question, force=True)
    new["agent"] = agent
    if agent["trace"]:
        new["more_available"] = False
        suggestions = suggest(store, dong, menus, summary, agent)  # Agent 결과까지 넣어 제안을 다시 만듦
        if suggestions:
            new["suggestions"] = suggestions
    else:  # 추가 질의를 하나도 못 함 → 버튼을 다시 눌러 볼 수 있게 둠
        new["more_available"] = True
        new["more_error"] = "추가 진단을 하지 못했어요. 잠시 후 다시 눌러 주세요."
    new["model"] = current_model()
    new["more_elapsed_sec"] = round(time.perf_counter() - started, 1)
    return new


def _summary_ok(summary) -> bool:
    """화면이 보낸 리포트의 summary가 Agent 실행에 필요한 모양인지 확인한다."""
    if not isinstance(summary, dict):
        return False
    mention = summary.get("mention")
    if not isinstance(mention, dict) or not isinstance(mention.get("rate"), (int, type(None))):
        return False
    return all(k in summary for k in ("by_type", "rank", "descriptions", "competitors"))


# ---------------------------------------------------------------- 혼자 실행

def _print_agent_and_suggestions(rep: dict) -> None:
    ag = rep["agent"]
    print(f"\n[Agent] {ag.get('reason_to_run', '')}")
    for t in ag.get("trace", []):
        r = t["result"]
        print(f"  - {t['tool_label']}: \"{t['question']}\" → 언급 {r['mentioned']}/{r['valid']}")
        print(f"    고른 이유: {t['why']}")
        if r["descriptions"]:
            print(f"    AI가 소개한 말: {r['descriptions'][0]}")
    for sk in ag.get("skipped", []):
        print(f"  (제외) {sk['tool']}: {sk['reason']}")
    if ag.get("error"):
        print(f"  (Agent 오류) {ag['error']}")

    print("\n[개선 제안]")
    if not rep["suggestions"]:
        print("  (개선 제안을 만들지 못했어요. 호출 한도에 걸렸을 수 있어요. 잠시 후 다시 실행해 보세요.)")
    for i, sg in enumerate(rep["suggestions"], 1):
        print(f"  {i}. {sg['title']}\n     {sg.get('detail', '')}\n     근거: {sg.get('evidence', '')}")


def main() -> None:
    print("진단 전체 실행 테스트")
    print(f"설정: 웹 검색 {'켬' if USE_SEARCH else '끔'} / 반복 {REPEAT}회 / 동시 {CONCURRENCY}개\n")
    store = input("상호: ").strip()
    region = input("지역 (시·구·동): ").strip()
    station = input("가까운 역 (없으면 Enter): ").strip()
    menus = input("대표 메뉴 1~3개, 쉼표로 구분: ").split(",")

    rep = run_diagnosis(store, region, menus, station)
    print(f"\n결과: {'성공' if rep['ok'] else '실패'} · {rep['elapsed_sec']}초")
    if not rep["ok"]:
        print(f"  {rep['error']}")
        for p in rep["problems"]:
            print(f"  - {p}")
        return

    s = rep["summary"]
    m = s["mention"]
    print(f"\n[언급률] 정상 답변 {m['valid']}개 중 {m['mentioned']}개 ({m['rate']}%)")
    for t, v in s["by_type"].items():
        print(f"  {t}: {v['mentioned']}/{v['valid']}")
    if s["rank"]["counted"]:
        print(f"[순위] 평균 {s['rank']['average']}위, 1위 {s['rank']['first_place']}회")
    for d in s["descriptions"]:
        print(f"[AI가 소개하는 말] \"{d['text']}\" ({d['count']}회)")
    for c in s["competitors"]:
        print(f"[함께 나온 가게] {c['name']} - 답변 {c['answers']}개, 메뉴형 {c['menu_answers']} ({c['description']})")
    _print_agent_and_suggestions(rep)

    if rep.get("more_available"):
        yn = input("\n'더 자세히 진단하기' 버튼을 눌러 볼까요? (y/N): ").strip().lower()
        if yn == "y":
            rep = run_more(rep)
            print(f"\n[더 자세히 진단하기] {rep.get('more_elapsed_sec', 0)}초")
            if rep.get("more_error"):
                print(f"  {rep['more_error']}")
            _print_agent_and_suggestions(rep)
    print(f"\n※ {rep['notice']}  (모델: {rep['model']})")

    out = "last_diagnosis.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print(f"전체 결과를 {out} 에 저장했습니다 (저장소에는 올리지 않음).")


if __name__ == "__main__":
    main()
