"""Gemini 호출을 한곳에 모은 파일.

기획서 4-1: "AI 호출은 파일 1개에 모음 + 결과 형식 통일"
→ 나중에 ChatGPT·Claude를 붙일 때도 이 파일과 같은 모양의 함수만 추가하면 됨.
"""

import os
import re
import threading
import time
from dataclasses import dataclass, field

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # 프로젝트 맨 위의 .env 파일에서 GEMINI_API_KEY 등을 읽어 옴

PROVIDER = "gemini"  # 2차에 ChatGPT·Claude를 붙이면 "openai", "anthropic" 등으로 구분

# 기본 모델: Gemini 3 계열.
# 이유: 웹 검색(Grounding) 월 5,000회 무료는 Gemini 3 이상 모델 기준 (2.5 이하는 요청 단위 과금이라 비용 계산이 달라짐)
# .env 의 GEMINI_MODEL 로 바꿀 수 있음 (예: Flash-Lite 계열). 최종 선택은 실측 후 확정 [실측 후 조정]
DEFAULT_MODEL = "gemini-3.8-flash"

# 호출 1회 시간 제한(초). 응답이 없을 때 끝없이 기다리지 않게 함
# (10/19 실측: 3.8-flash 첫 호출이 2분 가까이 응답 없음)
TIMEOUT_SEC = int(os.getenv("GEMINI_TIMEOUT_SEC", "60"))

# 분당 호출 한도(429)에 걸렸을 때 기다렸다가 다시 시도할 횟수
# (10/19: 무료 키 gemini-3.5-flash-lite는 분당 15회 → 진단 1회 중 Agent 단계에서 429 발생)
RATE_LIMIT_RETRIES = int(os.getenv("GEMINI_RATE_LIMIT_RETRIES", "3"))

_client = None  # 처음 호출할 때 한 번만 만들고 재사용
_client_lock = threading.Lock()  # 동시 호출 때 연결 객체가 두 번 만들어지지 않게


def _get_client() -> genai.Client:
    global _client
    with _client_lock:
        if _client is not None:
            return _client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY가 없습니다. .env.example 을 복사해 .env 를 만들고 키를 넣어 주세요."
            )
        _client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=TIMEOUT_SEC * 1000),  # 밀리초 단위
        )
        return _client


@dataclass
class GeminiResult:
    """모든 AI 호출 결과를 같은 모양으로 돌려주기 위한 상자."""

    ok: bool                      # 호출 성공 여부
    provider: str = PROVIDER      # 어느 회사 AI인지 (gemini / 나중에 openai, anthropic)
    model: str = ""               # 실제 사용한 모델 이름
    text: str = ""                # 답변 본문
    sources: list = field(default_factory=list)  # 웹 검색 사용 시 인용된 사이트 주소
    elapsed: float = 0.0          # 걸린 시간(초) → 300초 제한 실측에 사용
    error: str = ""               # 실패 이유


def _rate_limit_wait(error: Exception) -> float | None:
    """분당 호출 한도 초과(429)면 기다릴 초를 돌려준다. 다른 오류거나 기다려도 소용없는 한도면 None.

    Google이 오류 안에 알려주는 retryDelay(예: '2s')를 쓰고, 없으면 5초.
    "limit: 0"(무료 키에 그 기능 할당량 자체가 없음)은 기다려도 안 풀리므로 None.
    """
    text = str(error)
    if "429" not in text and "RESOURCE_EXHAUSTED" not in text:
        return None
    if re.search(r"limit:\s*0\b", text) or "PerDay" in text:
        return None
    m = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s", text) or re.search(r"retry in (\d+(?:\.\d+)?)s", text)
    wait = float(m.group(1)) + 1 if m else 5.0
    return min(max(wait, 2.0), 30.0)


def _call_with_retry(call, retries: int):
    """call()을 실행하고, 실패하면 다시 시도한다.
    - 분당 한도(429): Google이 알려준 시간만큼 기다렸다가 최대 RATE_LIMIT_RETRIES번
    - 그 밖의 오류: 1초 쉬고 최대 retries번
    성공하면 (결과, ""), 끝내 실패하면 (None, 마지막 오류 문장)
    """
    normal = limited = 0
    while True:
        try:
            return call(), ""
        except Exception as e:  # 네트워크 오류, 한도 초과 등
            last_error = f"{type(e).__name__}: {e}"
            wait = _rate_limit_wait(e)
            if wait is not None and limited < RATE_LIMIT_RETRIES:
                limited += 1
                time.sleep(wait)
                continue
            if wait is None and normal < retries:
                normal += 1
                time.sleep(1)
                continue
            return None, last_error


def ask_gemini(
    prompt: str,
    temperature: float | None = None,
    use_search: bool = False,
    json_output: bool = False,
    retries: int = 1,
) -> GeminiResult:
    """Gemini에 프롬프트를 보내고 결과를 GeminiResult로 돌려준다.

    temperature: None이면 모델 기본값 (손님 질문 재현용). 분석은 0, 질문 생성은 0.7 예정.
    use_search : 웹 검색(Grounding) 사용 여부. 손님 질문 질의 단계에서만 켬.
    json_output: JSON으로만 답하게 함. 질문 생성·답변 분석 단계에서 사용.
                 (웹 검색과 JSON 강제를 함께 쓰지 않음 — 질의 단계는 자유 문장이 필요)
    retries    : 실패 시 다시 시도할 횟수 (측정기준 4장: 1회)
    """
    model = os.getenv("GEMINI_MODEL") or DEFAULT_MODEL

    config_args = {}
    if temperature is not None:
        config_args["temperature"] = temperature
    if use_search:
        config_args["tools"] = [types.Tool(google_search=types.GoogleSearch())]
    if json_output:
        config_args["response_mime_type"] = "application/json"
    config = types.GenerateContentConfig(**config_args)

    start = time.perf_counter()
    response, error = _call_with_retry(
        lambda: _get_client().models.generate_content(model=model, contents=prompt, config=config),
        retries,
    )
    if response is None:
        return GeminiResult(ok=False, model=model, error=error)
    return GeminiResult(
        ok=True,
        model=model,
        text=(response.text or "").strip(),
        sources=_extract_sources(response),
        elapsed=round(time.perf_counter() - start, 2),  # 한도 대기 시간 포함
    )


def _extract_sources(response) -> list:
    """웹 검색을 썼을 때 답변에 인용된 사이트 주소를 꺼낸다. 없으면 빈 목록."""
    try:
        meta = response.candidates[0].grounding_metadata
        if not meta or not meta.grounding_chunks:
            return []
        return [c.web.uri for c in meta.grounding_chunks if c.web and c.web.uri]
    except (AttributeError, IndexError, TypeError):
        return []


@dataclass
class ToolChoice:
    """Gemini가 함수 호출(function calling)로 고른 도구 목록."""

    ok: bool
    calls: list = field(default_factory=list)  # [{"name": "도구 이름", "args": {...}}]
    text: str = ""        # 도구 대신 글로 답한 경우의 내용
    provider: str = PROVIDER
    model: str = ""
    elapsed: float = 0.0
    error: str = ""


def choose_tools(prompt: str, functions: list[dict], temperature: float = 0, retries: int = 1) -> ToolChoice:
    """함수 목록을 Gemini에 주고, 어떤 함수를 어떤 값으로 부를지 Gemini가 고르게 한다 (AI Agent의 핵심).

    functions: [{"name": ..., "description": ..., "parameters": JSON 스키마}]
    - 함수를 실제로 실행하지는 않음. 고른 결과(이름과 값)만 돌려주고, 실행은 호출한 쪽(ai/agent.py)이 함
    - mode="ANY": 반드시 함수 중 하나 이상을 고르게 함
    """
    model = os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
    declarations = [
        types.FunctionDeclaration(
            name=f["name"], description=f["description"], parameters_json_schema=f["parameters"]
        )
        for f in functions
    ]
    config = types.GenerateContentConfig(
        temperature=temperature,
        tools=[types.Tool(function_declarations=declarations)],
        tool_config=types.ToolConfig(function_calling_config=types.FunctionCallingConfig(mode="ANY")),
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    start = time.perf_counter()
    response, error = _call_with_retry(
        lambda: _get_client().models.generate_content(model=model, contents=prompt, config=config),
        retries,
    )
    if response is None:
        return ToolChoice(ok=False, model=model, error=error)
    calls = [{"name": c.name, "args": dict(c.args or {})} for c in (response.function_calls or [])]
    text = ""
    try:
        text = (response.text or "").strip()
    except (ValueError, AttributeError):
        pass  # 함수 호출만 있는 응답은 text가 없을 수 있음
    return ToolChoice(ok=True, calls=calls, text=text, model=model,
                      elapsed=round(time.perf_counter() - start, 2))
