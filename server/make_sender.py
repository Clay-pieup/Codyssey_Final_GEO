"""진단 결과를 Make 웹훅으로 보낸다 → Make가 구글 시트 기록 + Gmail 발송.

근거: docs/ARCHITECTURE.md 5장 (보낼 칸 목록), 기획서 4-4 (시트 분리, 이메일은 연락처 시트에만)
- Make에서 클릭으로 연결하기 쉽게 모든 값을 한 단계짜리 글자·숫자로 바꿔 보낸다
- 보내기에 실패해도 진단 결과는 화면에 그대로 응답한다 (delivery.error에만 기록)
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))  # 한국 시각
TIMEOUT_SEC = 10  # Make가 응답하지 않을 때 오래 기다리지 않음


def build_payload(report: dict, event: str, email: str) -> dict:
    """리포트(dict)에서 Make로 보낼 칸만 골라 한 줄짜리 값으로 만든다."""
    inp = report.get("input") or {}
    summary = report.get("summary") or {}
    mention = summary.get("mention") or {}
    agent = report.get("agent") or {}

    by_type = " · ".join(
        f"{name} {v.get('mentioned', 0)}/{v.get('valid', 0)}"
        for name, v in (summary.get("by_type") or {}).items()
    )

    # 질문별 결과: 같은 질문의 답변들을 모아 "언급/정상 답변" 수를 셈 (시트에는 답변 원문 대신 이 줄만 기록, 10/21 결정)
    per_question = {}
    for a in report.get("answers") or []:
        row = per_question.setdefault(a.get("question_id"), {"text": a.get("question", ""), "hit": 0, "valid": 0})
        if a.get("status") == "ok":
            row["valid"] += 1
            row["hit"] += 1 if a.get("mentioned") else 0
    questions_text = "\n".join(f"{qid} {r['text']} → {r['hit']}/{r['valid']}" for qid, r in per_question.items())

    agent_text = "\n".join(
        f"{t.get('tool_label', '')}: {t.get('question', '')} → "
        f"{(t.get('result') or {}).get('mentioned', 0)}/{(t.get('result') or {}).get('valid', 0)} (이유: {t.get('why', '')})"
        for t in agent.get("trace") or []
    )
    suggestions_text = "\n".join(
        f"{i}. {s.get('title', '')} - {s.get('detail', '')} (근거: {s.get('evidence', '')})"
        for i, s in enumerate(report.get("suggestions") or [], 1)
    )

    return {
        "event": event,
        "diagnosed_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "store": inp.get("store", ""),
        "region": inp.get("region", ""),
        "station": inp.get("station", ""),
        "menus": ", ".join(inp.get("menus") or []),
        "mention_rate": mention.get("rate"),
        "mention_text": f"정상 답변 {mention.get('valid', 0)}개 중 {mention.get('mentioned', 0)}개 ({mention.get('rate')}%)",
        "by_type_text": by_type,
        "competitors_text": ", ".join(c.get("name", "") for c in summary.get("competitors") or []),
        "questions_text": questions_text,
        "agent_trigger": agent.get("trigger", ""),
        "agent_text": agent_text,
        "suggestions_text": suggestions_text,
        "notice": report.get("notice", ""),
        "low_reliability": bool(summary.get("low_reliability")),
        "model": report.get("model", ""),
        "email": email,              # 동의한 이메일만 (아니면 빈칸) → Make가 빈칸이면 메일·연락처 단계를 건너뜀
        "consent": bool(email),
    }


def send_to_make(report: dict, event: str, email: str) -> dict:
    """성공한 진단만 Make로 보낸다. 돌려주는 값은 화면 응답의 delivery 칸이 된다."""
    delivery = {"requested": bool(email), "sent": False, "error": ""}
    if not report.get("ok"):
        delivery["error"] = "진단이 실패해서 보내지 않음"
        return delivery

    url = os.getenv("MAKE_WEBHOOK_URL", "").strip()
    if not url:
        delivery["error"] = "MAKE_WEBHOOK_URL이 설정되지 않음"
        return delivery

    body = json.dumps(build_payload(report, event, email), ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, method="POST", headers={"Content-Type": "application/json; charset=utf-8"}
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SEC) as response:
            delivery["sent"] = 200 <= response.status < 300
            if not delivery["sent"]:
                delivery["error"] = f"Make 응답 {response.status}"
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        delivery["error"] = f"Make 전송 실패: {type(e).__name__}"  # 주소·이메일이 로그에 남지 않게 종류만 기록
    return delivery
