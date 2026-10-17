"""ai/prompts/ 폴더의 프롬프트 파일을 읽고 빈칸을 채운다.

프롬프트를 코드 밖 파일로 분리한 이유 (팀 체크리스트 3.3):
- 프롬프트만 고칠 때 코드를 건드리지 않아도 됨
- 바꿀 때마다 ai/prompts/CHANGELOG.md 에 이유를 남겨 서면 심사 근거로 사용

빈칸은 $이름 형식으로 씀 (예: $dong).
{ } 를 쓰지 않는 이유: 프롬프트 안의 JSON 예시 {"questions": ...} 와 헷갈리지 않게 하려고.
"""

from pathlib import Path
from string import Template

PROMPT_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str, **values) -> str:
    """프롬프트 파일을 읽어 $빈칸을 values로 채워 돌려준다.

    예: load_prompt("question_generation", dong="망원동", station="망원역", ...)
    채우지 않은 빈칸이 있으면 바로 오류를 내서 실수를 일찍 발견하게 함.
    """
    path = PROMPT_DIR / f"{name}.md"
    text = path.read_text(encoding="utf-8")

    # 파일 맨 위의 설명 부분(--- 위)은 사람용이라 AI에 보내지 않음
    if "\n---\n" in text:
        text = text.split("\n---\n", 1)[1]

    return Template(text).substitute(**values).strip()
