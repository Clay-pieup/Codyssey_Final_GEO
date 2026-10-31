"""결과 리포트 팝업의 사장님 의견을 확인하고 피드백 저장 주소로 보낸다.

근거: docs/ARCHITECTURE.md 5장 (POST /api/feedback), 진행 기록 10/31 (피드백 팝업 결정)
- 문항은 리포트 영역(결과 이해, AI가 소개한 말, 함께 나온 가게, 개선 제안)에 맞춘 5개
- 의견 시트에는 이름·이메일을 넣지 않는다 (진단결과·연락처 시트를 나눈 것과 같은 원칙). 이름·이메일은 리포트 메일 발송(Make)에만 쓴다
- 저장 주소(FEEDBACK_WEBHOOK_URL)는 구글 Apps Script 웹 앱(automation/feedback_sheet.gs). 시트에 적으면 "ok"라고 답한다
- 저장 성공은 그 "ok" 답을 받았을 때만 (10/31: 구글 로그인 화면이 대신 열려도 성공으로 착각하던 문제 수정)
- 실패하면 Vercel 로그에 "[feedback] 이유" 한 줄을 남긴다. 주소·의견 내용은 남기지 않는다 (사장님 화면은 그대로)
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
TIMEOUT_SEC = 10
MAX_COMMENT = 300
MAX_NAME = 20

# 고르는 문항의 보기 (화면 버튼과 같아야 함)
CHOICES = {
    "accuracy": ("맞음", "일부 맞음", "틀림", "소개 없음"),               # "AI가 우리 가게를 소개한 말"이 실제와 맞았나
    "competitors": ("비슷해요", "일부 비슷해요", "달라요", "잘 모르겠어요"),  # "함께 나온 가게"가 실제 경쟁 가게와 비슷했나
    "useful": ("있음", "없음"),                                        # 해 볼 만한 개선 제안이 있었나
}


def _short_text(value, limit: int) -> str:
    """글자만 받고 길이를 자른다. =, +, -, @로 시작하면 시트가 수식으로 실행하지 않게 앞에 '를 붙인다."""
    text = value.strip()[:limit] if isinstance(value, str) else ""
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


def check_name(value) -> str:
    """이름은 1~20자 글자만. 아니면 빈 문자열."""
    return _short_text(value, MAX_NAME) if isinstance(value, str) and value.strip() else ""


def check_feedback(data: dict, report: dict) -> tuple[dict | None, list[str]]:
    """화면이 보낸 의견을 확인한다. 통과하면 (저장할 값, []), 아니면 (None, 문제 목록)."""
    problems = []
    clean = {}

    clarity = data.get("clarity")
    # True/False도 숫자로 취급되는 파이썬 특성 때문에 bool은 따로 막는다
    if not (isinstance(clarity, int) and not isinstance(clarity, bool) and 1 <= clarity <= 5):
        problems.append("clarity: 1~5 중에서 골라 주세요")
        clarity = None
    clean["clarity"] = clarity

    for key, options in CHOICES.items():
        value = data.get(key)
        if value not in options:
            problems.append(f"{key}: 보기 중에서 골라 주세요")
        clean[key] = value if value in options else ""

    clean["comment"] = _short_text(data.get("comment"), MAX_COMMENT)

    # 어떤 진단을 보고 남긴 의견인지 대조용 (리포트에서 서버가 직접 꺼냄. 이름·이메일은 넣지 않음)
    inp = report.get("input") or {}
    mention = (report.get("summary") or {}).get("mention") or {}
    clean.update({
        "store": _short_text(inp.get("store"), 30),
        "region": _short_text(inp.get("region"), 60),
        "menus": _short_text(", ".join(inp.get("menus") or []), 60),
        "mention_rate": mention.get("rate") if isinstance(mention.get("rate"), (int, float)) else "",
        "agent_ran": bool((report.get("agent") or {}).get("ran")),
    })
    return (None if problems else clean), problems


def send_feedback(feedback: dict) -> dict:
    """의견을 피드백 저장 주소로 보낸다. {"ok": 저장 성공 여부, "error": 안내 문장}"""
    failed = {"ok": False, "error": "의견을 저장하지 못했어요."}
    url = os.getenv("FEEDBACK_WEBHOOK_URL", "").strip()
    if not url:
        print("[feedback] FEEDBACK_WEBHOOK_URL이 비어 있음 → Vercel 환경 변수 저장 후 Redeploy 했는지 확인")
        return {"ok": False, "error": "의견 저장이 아직 준비되지 않았어요."}

    payload = {"event": "feedback", "submitted_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M"), **feedback}
    request = urllib.request.Request(
        url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        # Apps Script는 기록한 뒤 다른 주소로 한 번 넘겨서(redirect) "ok"를 보여 준다. urlopen이 그 주소까지 따라감
        with urllib.request.urlopen(request, timeout=TIMEOUT_SEC) as response:
            landed = urllib.parse.urlparse(response.geturl()).hostname or ""  # 마지막에 도착한 곳 (주소 뒷부분은 버림)
            answer = response.read(200).decode("utf-8", "replace").strip()
    except urllib.error.HTTPError as e:
        print(f"[feedback] 저장 주소 응답 {e.code} → Apps Script 웹 앱 주소(/exec)가 맞는지 확인")
        return failed
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"[feedback] 저장 주소에 연결 실패: {type(e).__name__}")
        return failed

    if answer == "ok":                                   # feedback_sheet.gs가 시트에 한 줄 적고 돌려주는 답
        return {"ok": True, "error": ""}
    if landed.endswith("accounts.google.com"):            # 공개 범위가 '모든 사용자'가 아니면 로그인 화면으로 감
        print("[feedback] 구글 로그인 화면으로 이동됨 → Apps Script 배포의 액세스 권한을 '모든 사용자'로")
    else:                                                 # 시트 기록 중 오류, 옛 버전 배포, 다른 주소 등
        print(f"[feedback] 'ok' 대신 다른 답을 받음 (도착한 곳: {landed}) → Apps Script 실행 기록과 배포 버전 확인")
    return failed
