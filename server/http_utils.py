"""요청 읽기·응답 보내기·이메일 확인. api/diagnose.py와 api/more.py가 함께 쓴다.

근거: docs/API_명세.md 1-3 (HTTP 상태), 1-1 (이메일은 동의했을 때만)
"""

import json
import re

MAX_BODY_BYTES = 2_000_000  # 요청 최대 2MB. 리포트를 다시 보내는 /api/more도 충분한 크기
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")  # 화면과 같은 규칙


def read_json(handler) -> tuple[dict | None, str]:
    """요청 본문을 JSON으로 읽는다. 성공하면 (dict, ""), 실패하면 (None, 이유)."""
    try:
        length = int(handler.headers.get("Content-Length") or 0)
    except ValueError:
        return None, "Content-Length가 숫자가 아님"
    if length <= 0:
        return None, "요청 본문이 비어 있음"
    if length > MAX_BODY_BYTES:
        return None, "요청이 너무 큼"
    try:
        data = json.loads(handler.rfile.read(length).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "JSON 형식이 아님"
    if not isinstance(data, dict):
        return None, "JSON 객체({ })가 아님"
    return data, ""


def send_json(handler, status: int, body: dict) -> None:
    """dict를 JSON으로 바꿔 응답한다. 한글이 깨지지 않게 utf-8로 보낸다."""
    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.send_header("Cache-Control", "no-store")  # 진단 결과는 저장해 두지 않음
    handler.end_headers()
    handler.wfile.write(raw)


def bad_request(handler, problem: str) -> None:
    send_json(handler, 400, {"ok": False, "error": "요청 형식이 올바르지 않아요.", "problems": [problem]})


def method_not_allowed(handler) -> None:
    send_json(handler, 405, {"ok": False, "error": "POST로 요청해 주세요.", "problems": []})


def server_error(handler) -> None:
    send_json(handler, 500, {"ok": False, "error": "진단 중 오류가 났어요. 잠시 후 다시 시도해 주세요.", "problems": []})


def consented_email(data: dict) -> str:
    """동의했고 형식이 맞는 이메일만 돌려준다. 아니면 빈 문자열 → Make에 이메일을 넘기지 않음."""
    email = data.get("email")
    if data.get("consent") is not True or not isinstance(email, str):
        return ""
    email = email.strip()
    return email if len(email) <= 254 and EMAIL_PATTERN.match(email) else ""
