"""Gemini 호출을 한곳에 모은 파일.

기획서 4-1: "AI 호출은 파일 1개에 모음 + 결과 형식 통일"
→ 나중에 ChatGPT·Claude를 붙일 때도 이 파일과 같은 모양의 함수만 추가하면 됨.
"""

import os
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

_client = None  # 처음 호출할 때 한 번만 만들고 재사용


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY가 없습니다. .env.example 을 복사해 .env 를 만들고 키를 넣어 주세요."
            )
        _client = genai.Client(api_key=api_key)
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

    last_error = ""
    for attempt in range(retries + 1):
        start = time.perf_counter()
        try:
            response = _get_client().models.generate_content(
                model=model, contents=prompt, config=config
            )
            elapsed = time.perf_counter() - start
            return GeminiResult(
                ok=True,
                model=model,
                text=(response.text or "").strip(),
                sources=_extract_sources(response),
                elapsed=round(elapsed, 2),
            )
        except Exception as e:  # 네트워크 오류, 한도 초과 등
            last_error = f"{type(e).__name__}: {e}"
            if attempt < retries:
                time.sleep(1)  # 잠깐 쉬고 다시 시도

    return GeminiResult(ok=False, model=model, error=last_error)


def _extract_sources(response) -> list:
    """웹 검색을 썼을 때 답변에 인용된 사이트 주소를 꺼낸다. 없으면 빈 목록."""
    try:
        meta = response.candidates[0].grounding_metadata
        if not meta or not meta.grounding_chunks:
            return []
        return [c.web.uri for c in meta.grounding_chunks if c.web and c.web.uri]
    except (AttributeError, IndexError, TypeError):
        return []
