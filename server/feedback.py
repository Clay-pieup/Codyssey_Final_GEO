"""결과 리포트 팝업의 사장님 피드백을 확인하고 피드백 저장 주소로 보낸다.

근거: docs/ARCHITECTURE.md 5장 (POST /api/feedback), 진행 기록 10/31 (피드백 팝업 결정)
- 이름·연락처는 받지 않는다 (G7). 가게·지역은 타깃 근거(G5)와 진단 결과 대조용
- 저장 주소(FEEDBACK_WEBHOOK_URL)는 JSON을 POST로 받는 곳이면 됨 (Make 웹훅 또는 구글 Apps Script 웹 앱)
- 보낼 때 실패하면 사장님께 "다시 보내 주세요"를 보여 주고, 주소·내용은 로그에 남기지 않는다
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
TIMEOUT_SEC = 10
MAX_COMMENT = 300

# 고르는 문항의 보기 (화면 버튼과 같아야 함). 사용자 피드백 기록 2장 설문 문항과 같은 내용
CHOICES = {
    "owner": ("예", "아니요"),                                              # 외식업 운영 여부 (G5 타깃 근거)
    "category": ("한식", "중식", "일식", "양식", "분식", "카페", "주점", "기타"),  # 업종
    "accuracy": ("맞음", "일부 맞음", "틀림", "소개 없음"),                     # AI가 소개한 말이 실제와 맞았나
    "useful": ("있음", "없음"),                                              # 해 볼 만한 개선 제안이 있었나
}
REQUIRED = ("owner", "clarity")


def _short_text(value, limit: int) -> str:
    """글자만 받고 길이를 자른다. =, +, -, @로 시작하면 시트가 수식으로 실행하지 않게 앞에 '를 붙인다."""
    text = value.strip()[:limit] if isinstance(value, str) else ""
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


def check_feedback(data: dict) -> tuple[dict | None, list[str]]:
    """화면이 보낸 피드백을 확인한다. 통과하면 (저장할 값, []), 아니면 (None, 문제 목록)."""
    problems = []
    clean = {}

    for key, options in CHOICES.items():
        value = data.get(key) or ""
        if value and value not in options:
            problems.append(f"{key}: 보기 중에서 골라 주세요")
        clean[key] = value

    clarity = data.get("clarity")
    # True/False도 숫자로 취급되는 파이썬 특성 때문에 bool은 따로 막는다
    if not (isinstance(clarity, int) and not isinstance(clarity, bool) and 1 <= clarity <= 5):
        clarity = None
    clean["clarity"] = clarity

    for key in REQUIRED:
        if not clean.get(key):
            problems.append(f"{key}: 꼭 답해 주세요")

    clean["comment"] = _short_text(data.get("comment"), MAX_COMMENT)

    # 진단 정보 (화면이 자동으로 붙임): 어떤 진단을 보고 남긴 의견인지 대조용
    context = data.get("context") if isinstance(data.get("context"), dict) else {}
    rate = context.get("mention_rate")
    clean.update({
        "store": _short_text(context.get("store"), 30),
        "region": _short_text(context.get("region"), 60),
        "mention_rate": rate if isinstance(rate, (int, float)) and not isinstance(rate, bool) else "",
        "agent_ran": bool(context.get("agent_ran")),
    })
    return (None if problems else clean), problems


def send_feedback(feedback: dict) -> dict:
    """피드백 저장 주소로 보낸다. 돌려주는 값이 화면 응답이 된다."""
    url = os.getenv("FEEDBACK_WEBHOOK_URL", "").strip()
    if not url:
        return {"ok": False, "error": "의견 저장이 아직 준비되지 않았어요. 잠시 후 다시 보내 주세요."}

    payload = {"event": "feedback", "submitted_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M"), **feedback}
    request = urllib.request.Request(
        url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SEC) as response:
            if 200 <= response.status < 300:
                return {"ok": True, "error": ""}
            print(f"[feedback] 저장 주소 응답 {response.status}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"[feedback] 저장 실패: {type(e).__name__}")  # 주소·의견 내용은 남기지 않음
    return {"ok": False, "error": "의견을 보내지 못했어요. 잠시 후 다시 보내 주세요."}
