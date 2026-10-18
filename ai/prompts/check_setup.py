"""환경이 제대로 준비됐는지 확인하는 스크립트.

실행 (프로젝트 맨 위 폴더에서):
    python -m ai.check_setup

1) 패키지 설치 확인  2) 프롬프트 파일 읽기 확인  3) API 키가 있으면 Gemini에 짧은 질문 1개를 보내 걸린 시간 표시
"""

import os
import sys


def main() -> None:
    print("1) 패키지 확인")
    try:
        import dotenv  # noqa: F401
        from google import genai  # noqa: F401
        print("   OK: google-genai, python-dotenv 설치됨")
    except ImportError as e:
        print(f"   실패: {e}\n   → pip install -r requirements.txt 를 먼저 실행하세요")
        sys.exit(1)

    print("2) 프롬프트 파일 확인")
    from ai.prompt_loader import load_prompt

    prompt = load_prompt(
        "question_generation",
        dong="망원동",
        station="망원역",
        menus="등심돈까스, 치즈돈까스",
        situations="혼밥·1인 식사, 데이트, 아이와 함께",
        conditions="주차, 예약 가능",
    )
    print(f"   OK: question_generation.md 읽음 ({len(prompt)}자, 빈칸 채우기 성공)")

    print("3) Gemini 호출 확인")
    from ai.gemini_client import ask_gemini

    if not os.getenv("GEMINI_API_KEY"):
        print("   건너뜀: .env 에 GEMINI_API_KEY 가 없습니다 (키를 받으면 다시 실행)")
        return

    result = ask_gemini("한 문장으로 인사해 줘.")
    if result.ok:
        print(f"   OK: {result.elapsed}초 걸림 → 답변: {result.text[:60]}")
    else:
        print(f"   실패: {result.error}")


if __name__ == "__main__":
    main()
