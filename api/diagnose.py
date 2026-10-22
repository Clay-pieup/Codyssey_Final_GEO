"""POST /api/diagnose — "진단 시작하기" 버튼.

흐름: 요청 읽기 → 형식 확인 → AI 진단(run_diagnosis) → Make로 결과 전달 → 리포트 응답
약속: docs/API_명세.md 1장 / 설명: docs/서버_해설.md
"""

import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler

# 프로젝트 맨 위 폴더를 import 경로에 추가 → ai/, server/ 폴더를 불러올 수 있게
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.diagnosis import run_diagnosis  # noqa: E402
from server.http_utils import (  # noqa: E402
    bad_request, consented_email, method_not_allowed, read_json, send_json, server_error,
)
from server.make_sender import send_to_make  # noqa: E402


def _text(data: dict, key: str) -> str | None:
    """문자열 칸을 꺼낸다. 없으면 "", 문자열이 아니면 None(형식 오류)."""
    value = data.get(key, "")
    if value is None:
        return ""
    return value if isinstance(value, str) else None


class handler(BaseHTTPRequestHandler):  # Vercel이 이 이름(handler)을 찾아 실행함

    def do_POST(self):
        data, problem = read_json(self)
        if data is None:
            return bad_request(self, problem)

        store, region, station = _text(data, "store"), _text(data, "region"), _text(data, "station")
        menus = data.get("menus")
        if None in (store, region, station):
            return bad_request(self, "store·region·station은 문자열이어야 함")
        if not isinstance(menus, list) or not all(isinstance(m, str) for m in menus):
            return bad_request(self, "menus는 문자열 목록이어야 함 (예: [\"칼국수\", \"만두\"])")

        try:
            # 상호·지역·메뉴 규칙(30자, "동" 포함, 1~3개)은 run_diagnosis가 AI를 부르기 전에 검사함
            report = run_diagnosis(store, region, menus, station)
            report["delivery"] = send_to_make(report, "diagnosis_completed", consented_email(data))
        except Exception:
            traceback.print_exc()  # Vercel 로그에만 남김 (화면에는 일반 안내 문장)
            return server_error(self)

        send_json(self, 200, report)  # 입력 오류·AI 실패도 200 + ok:false (API 명세 1-3)

    def do_GET(self):
        method_not_allowed(self)
