"""POST /api/more — "더 자세히 진단하기" 버튼.

흐름: 요청 읽기 → 1차 리포트 확인 → Agent 추가 진단(run_more) → Make로 결과 전달 → 리포트 응답
서버는 1차 진단을 기억하지 못하므로 화면이 1차 리포트를 그대로 다시 보낸다.
약속·설명: docs/ARCHITECTURE.md 2·5장
"""

import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.diagnosis import run_more  # noqa: E402
from server.http_utils import (  # noqa: E402
    bad_request, consented_email, method_not_allowed, read_json, send_json, server_error,
)
from server.make_sender import send_to_make  # noqa: E402


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        data, problem = read_json(self)
        if data is None:
            return bad_request(self, problem)
        if not isinstance(data.get("report"), dict):
            return bad_request(self, "report(1차 진단 결과)가 없음")

        try:
            # 이미 추가 진단을 한 리포트, 깨진 리포트는 run_more가 실행하지 않고 more_error에 이유를 넣음
            report = run_more(data["report"])
            if report.get("ok") and not report.get("more_error"):  # 추가 진단이 실제로 된 경우만 메일 재발송
                report["delivery"] = send_to_make(report, "more_completed", consented_email(data))
            else:
                report["delivery"] = {"requested": False, "sent": False, "error": "추가 진단이 없어 보내지 않음"}
        except Exception:
            traceback.print_exc()
            return server_error(self)

        send_json(self, 200, report)

    def do_GET(self):
        method_not_allowed(self)
