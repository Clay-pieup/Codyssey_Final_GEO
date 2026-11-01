"""POST /api/feedback — 결과 리포트에서 사장님 의견 받기 + 리포트 메일 보내기.

요청의 mode에 따라 세 가지 (11/1 "한 줄 질문 + 메일 보관" 설계):
- "quick": 리포트 중간 한 줄 질문에 탭 한 번 → 의견만 피드백 시트로 (이름·이메일 없음)
- "mail":  한 줄 질문 뒤 "메일로 보관할까요?" → 이메일·동의(이름은 선택)를 받아 리포트를 Make로 → 연락처 시트 + Gmail
- "full":  맨 아래 5문항 팝업 → 의견을 피드백 시트로, 이메일·동의가 함께 오면 리포트 메일도 (이미 메일을 받았으면 이메일 없이)
약속: docs/ARCHITECTURE.md 5장
- 서버는 진단을 기억하지 못하므로 화면이 리포트를 통째로 다시 보낸다 ("더 자세히 진단하기"와 같은 방식)
- 이메일은 개인정보 동의가 정확히 true일 때만 쓴다 (consented_email). 이름은 선택
"""

import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.feedback import check_feedback, check_name, send_feedback  # noqa: E402
from server.http_utils import (  # noqa: E402
    bad_request, consented_email, method_not_allowed, read_json, send_json, server_error,
)
from server.make_sender import send_to_make  # noqa: E402

MODES = ("quick", "mail", "full")
NOT_SENT = {"sent": False}


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        data, problem = read_json(self)
        if data is None:
            return bad_request(self, problem)
        report = data.get("report")
        if not isinstance(report, dict) or not report.get("ok"):
            return bad_request(self, "report(진단 결과)가 없음")
        mode = data.get("mode") or "full"
        if mode not in MODES:
            return bad_request(self, "mode는 quick·mail·full 중 하나")

        name = check_name(data.get("name"))   # 선택 (없으면 빈칸)
        email = consented_email(data)
        problems = []
        feedback = None
        if mode != "mail":
            feedback, problems = check_feedback(data, report, quick=(mode == "quick"))
        if mode == "mail" and not email:
            problems.append("email: 이메일과 개인정보 동의를 확인해 주세요")
        if mode == "full" and data.get("email") and not email:
            problems.append("email: 이메일 형식과 개인정보 동의를 확인해 주세요")   # 이메일을 적었는데 동의가 없거나 형식이 틀림
        if problems:
            # 진단과 같은 약속: 입력 문제는 200 + ok:false, 화면은 error 문장을 보여 줌
            return send_json(self, 200, {"ok": False, "error": "답과 입력 칸을 다시 확인해 주세요.", "problems": problems})

        try:
            saved = send_feedback(feedback) if feedback else {"ok": False}                    # ① 의견 → 피드백 시트
            delivery = send_to_make(report, "feedback_report", email, name) if email else NOT_SENT   # ② 리포트 → Make → 연락처 시트 + Gmail
        except Exception:
            traceback.print_exc()
            return server_error(self)

        ok = delivery["sent"] if mode == "mail" else (saved["ok"] or delivery["sent"])
        send_json(self, 200, {
            "ok": ok,
            "feedback_saved": saved["ok"],
            "mail_sent": delivery["sent"],
            "error": "" if ok else ("리포트 메일을 보내지 못했어요. 잠시 후 다시 눌러 주세요." if mode == "mail"
                                    else "의견을 보내지 못했어요. 잠시 후 다시 보내 주세요."),
        })

    def do_GET(self):
        method_not_allowed(self)
