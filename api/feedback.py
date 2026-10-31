"""POST /api/feedback — 결과 리포트의 "사장님 의견" 팝업 [보내기] 버튼.

흐름: 요청 읽기 → 답 확인(server/feedback.py) → 피드백 저장 주소로 전달 → 결과 응답
약속: docs/ARCHITECTURE.md 5장
"""

import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.feedback import check_feedback, send_feedback  # noqa: E402
from server.http_utils import bad_request, method_not_allowed, read_json, send_json, server_error  # noqa: E402


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        data, problem = read_json(self)
        if data is None:
            return bad_request(self, problem)

        feedback, problems = check_feedback(data)
        if feedback is None:
            # 진단과 같은 약속: 입력 문제는 200 + ok:false, 화면은 error 문장을 보여 줌
            return send_json(self, 200, {"ok": False, "error": "답을 다시 확인해 주세요.", "problems": problems})

        try:
            result = send_feedback(feedback)
        except Exception:
            traceback.print_exc()
            return server_error(self)
        send_json(self, 200, result)

    def do_GET(self):
        method_not_allowed(self)
