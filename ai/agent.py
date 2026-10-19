"""AI Agent: 언급률이 낮을 때 추가로 던질 질문을 AI가 직접 골라 실행한다.

근거: 기획서 3-1, 평가기준 G3 "LLM이 2개 이상의 도구·함수 중 호출 대상을 스스로 정함"
- 질문 도구 3개를 각각 함수로 정의 → Gemini 함수 호출(function calling)로 AI가 1~2개를 고름
- 고른 도구로 질문을 실제로 던지고(반복 REPEAT회), 결과를 분석해 판단 이유와 함께 기록
- 추가 질의는 1회(판단 1번)로 제한 → 호출 수와 시간이 늘어나는 것을 막음 (기획서 3-1)

혼자 실행해 보기:  python -m ai.diagnosis  (언급률이 30% 미만인 가게를 넣으면 Agent가 실행됨)
"""

import json
import os

from ai.gemini_client import choose_tools
from ai.prompt_loader import load_prompt
from ai.text_utils import normalize, store_key

THRESHOLD = int(os.getenv("AGENT_THRESHOLD", "30"))  # 언급률(%) 기준 [실측 후 조정]
MAX_TOOLS = 2  # 추가 질문 최대 2개 (기획서 3-1)

# 질문 도구 3개. AI는 이 중에서 고르고, 질문 문장과 이유를 값(args)으로 채워 넘긴다.
TOOLS = [
    {
        "name": "ask_direct_name",
        "label": "직접 지명형",
        "description": "가게 이름을 직접 넣어 묻는다. AI가 이 가게를 아예 모르는지, 알지만 추천하지 않는지 구분할 때 쓴다.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "상호와 지역을 넣은 손님 질문. 예: 망원동 행복돈까스 어때?"},
                "why": {"type": "string", "description": "이 도구를 고른 이유. 기본 진단 결과의 숫자나 가게 이름을 근거로 한 문장"},
            },
            "required": ["question", "why"],
        },
    },
    {
        "name": "ask_competitor_compare",
        "label": "경쟁 비교형",
        "description": "같은 메뉴·지역의 가게들을 비교하게 묻는다. 함께 자주 나온 경쟁 가게 대비 우리 가게의 위치를 확인할 때 쓴다.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "상호 없이 지역과 메뉴를 넣은 비교 질문. 예: 망원동 돈까스집 중 어디가 나아?"},
                "competitor": {"type": "string", "description": "비교의 기준이 된 경쟁 가게 이름 (기본 진단 결과의 competitors 중 하나)"},
                "why": {"type": "string", "description": "이 도구를 고른 이유. 기본 진단 결과의 숫자나 가게 이름을 근거로 한 문장"},
            },
            "required": ["question", "why"],
        },
    },
    {
        "name": "ask_situation_detail",
        "label": "상황 세분형",
        "description": "손님 상황을 더 좁혀서 묻는다. 어떤 상황에서 노출되고 어떤 상황에서 안 되는지 확인할 때 쓴다.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "상호 없이 지역과 구체적인 손님 상황을 넣은 질문. 예: 망원역 혼밥 점심 어디가 좋아?"},
                "situation": {"type": "string", "description": "좁혀 본 손님 상황. 예: 혼밥 점심"},
                "why": {"type": "string", "description": "이 도구를 고른 이유. 기본 진단 결과의 숫자나 가게 이름을 근거로 한 문장"},
            },
            "required": ["question", "why"],
        },
    },
]
TOOL_BY_NAME = {t["name"]: t for t in TOOLS}


def _check_call(name: str, question: str, store: str, dong: str, station: str) -> str:
    """AI가 만든 질문이 규칙을 지키는지 확인한다. 문제가 있으면 이유 문장, 없으면 빈 문자열."""
    if name not in TOOL_BY_NAME:
        return f"정의되지 않은 도구: {name}"
    if not question.strip():
        return "질문이 비어 있음"
    if not ((dong and dong in question) or (station and station.removesuffix("역") in question)):
        return "질문에 지역이 없음"
    has_store = store_key(store) in normalize(question)
    if name == "ask_direct_name" and not has_store:
        return "직접 지명형인데 상호가 없음"
    if name != "ask_direct_name" and has_store:
        return "상호가 들어가면 안 되는 도구인데 상호가 있음"
    return ""


def run_agent(store: str, dong: str, station: str, menus: list[str], summary: dict,
              run_queries, analyze_question) -> dict:
    """언급률을 보고 Agent를 실행할지 정하고, 실행하면 AI가 고른 도구로 추가 질의를 한다.

    run_queries, analyze_question: ai/diagnosis.py의 함수를 받아 그대로 사용 (질의·분석 방식 통일)
    """
    rate = summary["mention"]["rate"]
    if rate is not None and rate >= THRESHOLD:
        return {"ran": False, "reason_to_run": f"언급률 {rate}% ≥ 기준 {THRESHOLD}% → 추가 질의 안 함",
                "trace": [], "skipped": []}

    agent = {"ran": True, "reason_to_run": f"언급률 {rate}% < 기준 {THRESHOLD}% → 추가 질의 실행",
             "trace": [], "skipped": [], "model": "", "error": ""}

    brief = {k: summary[k] for k in ("mention", "by_type", "rank", "descriptions", "competitors")}
    prompt = load_prompt(
        "agent_decision", store_name=store, dong=dong, station=station or "없음",
        menus=", ".join(menus), summary=json.dumps(brief, ensure_ascii=False, indent=1),
    )
    choice = choose_tools(prompt, [{k: t[k] for k in ("name", "description", "parameters")} for t in TOOLS])
    agent["model"] = choice.model
    if not choice.ok or not choice.calls:
        agent["error"] = choice.error or "AI가 도구를 고르지 않음"
        return agent

    # 고른 도구 정리: 규칙 검사, 같은 도구 중복 제거, 최대 2개
    picked, seen = [], set()
    for c in choice.calls:
        name, args = c["name"], c["args"]
        question = str(args.get("question", "")).strip()
        problem = _check_call(name, question, store, dong, station)
        if problem or name in seen or len(picked) >= MAX_TOOLS:
            agent["skipped"].append({"tool": name, "question": question,
                                     "reason": problem or ("같은 도구 중복" if name in seen else "최대 2개 초과")})
            continue
        seen.add(name)
        picked.append({"id": f"a{len(picked) + 1}", "type": TOOL_BY_NAME[name]["label"], "text": question,
                       "tool": name, "args": args})

    if not picked:
        agent["error"] = "AI가 고른 질문이 모두 규칙 검사에서 걸림"
        return agent

    # 실행: 고른 질문을 기본 진단과 같은 방식으로 질의·분석
    answers = run_queries(picked)
    for p in picked:
        part = [a for a in answers if a["question_id"] == p["id"]]
        analyze_question(store, dong, p["text"], part)
        valid = [a for a in part if a["status"] == "ok"]
        hits = [a for a in valid if a["mentioned"]]
        others = sorted({s["name"] for a in valid for s in a["other_stores"]})[:5]
        agent["trace"].append({
            "tool": p["tool"],
            "tool_label": p["type"],
            "why": str(p["args"].get("why", "")).strip(),
            "question": p["text"],
            "args": {k: v for k, v in p["args"].items() if k not in ("question", "why")},
            "result": {
                "mentioned": len(hits), "valid": len(valid),
                "descriptions": [a["description"] for a in hits if a["description"]][:3],
                "other_stores": others,
            },
            "answers": part,
        })
    return agent
