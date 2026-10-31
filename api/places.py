"""POST /api/places — 입력 화면의 "가게 검색" 버튼.

흐름: 요청 읽기 → 검색어 확인 → 네이버 지역 검색(server/naver_places.py) → 목록 응답
약속: docs/ARCHITECTURE.md 5장
"""

import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.http_utils import bad_request, method_not_allowed, read_json, send_json, server_error  # noqa: E402
from server.naver_places import search_places  # noqa: E402

MIN_LEN, MAX_LEN = 2, 40  # 한 글자 검색은 결과가 너무 넓고, 긴 문장은 가게 이름이 아님


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        data, problem = read_json(self)
        if data is None:
            return bad_request(self, problem)
        query = data.get("query")
        if not isinstance(query, str):
            return bad_request(self, "query는 문자열이어야 함")
        query = query.strip()
        if not MIN_LEN <= len(query) <= MAX_LEN:
            # 입력 오류도 진단과 같이 200 + ok:false (화면이 한 가지 모양만 처리)
            return send_json(self, 200, {"ok": False, "error": f"가게 이름을 {MIN_LEN}~{MAX_LEN}자로 입력해 주세요.", "places": []})

        try:
            result = search_places(query)
        except Exception:
            traceback.print_exc()
            return server_error(self)
        send_json(self, 200, result)

    def do_GET(self):
        method_not_allowed(self)
