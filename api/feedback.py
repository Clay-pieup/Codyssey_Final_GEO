"""POST /api/feedback — 결과 리포트의 사장님 의견 팝업 [의견 보내고 리포트 받기] 버튼.

흐름: 요청 읽기 → 의견·이름·이메일·동의 확인 → ① 의견을 피드백 시트로 ② 리포트를 Make로 보내 메일 발송 → 결과 응답
약속: docs/ARCHITECTURE.md 5장
- 서버는 진단을 기억하지 못하므로 화면이 리포트를 통째로 다시 보낸다 ("더 자세히 진단하기"와 같은 방식)
- 이메일은 개인정보 동의가 정확히 true일 때만 쓴다 (consented_email)
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


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        data, problem = read_json(self)
        if data is None:
            return bad_request(self, problem)
        report = data.get("report")
        if not isinstance(report, dict) or not report.get("ok"):
            return bad_request(self, "report(진단 결과)가 없음")

        feedback, problems = check_feedback(data, report)
        name = check_name(data.get("name"))
        email = consented_email(data)
        if not name:
            problems.append("name: 이름을 입력해 주세요")
        if not email:
            problems.append("email: 이메일과 개인정보 동의를 확인해 주세요")
        if problems:
            # 진단과 같은 약속: 입력 문제는 200 + ok:false, 화면은 error 문장을 보여 줌
            return send_json(self, 200, {"ok": False, "error": "답과 입력 칸을 다시 확인해 주세요.", "problems": problems})

        try:
            saved = send_feedback(feedback)                                   # ① 의견 → 피드백 시트 (이름·이메일 없음)
            delivery = send_to_make(report, "feedback_report", email, name)   # ② 리포트 → Make → 연락처 시트 + Gmail
        except Exception:
            traceback.print_exc()
            return server_error(self)

        ok = saved["ok"] or delivery["sent"]
        send_json(self, 200, {
            "ok": ok,
            "feedback_saved": saved["ok"],
            "mail_sent": delivery["sent"],
            "error": "" if ok else "의견을 보내지 못했어요. 잠시 후 다시 보내 주세요.",
        })

    def do_GET(self):
        method_not_allowed(self)
