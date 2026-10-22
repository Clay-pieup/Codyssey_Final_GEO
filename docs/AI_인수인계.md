# AI 진단 인수인계 메모 (10/22 통합일용)

> AI 담당 작성 · 2026-10-20 · AI 담당은 10/22(목) 통합일에 자리에 없습니다. 통합 중 AI 부분에서 막히면 이 문서부터 봐 주세요.
> 자세한 입출력: [`AI_진단_입출력.md`](AI_진단_입출력.md) · 기능별 설명: [`AI_활용명세.md`](AI_활용명세.md)

---

## 1. 한 줄 요약

- 서버는 `ai/diagnosis.py`의 함수 2개만 부르면 됩니다. 둘 다 JSON으로 바꿀 수 있는 dict(리포트)를 돌려줍니다.
  - `run_diagnosis(store, region, menus, station)` → 진단 1회 (언급률 30% 미만이면 Agent까지 자동)
  - `run_more(report)` → "더 자세히 진단하기" 버튼 (화면이 받은 리포트를 그대로 다시 보냄)
- 이메일은 AI 쪽에 넘기지 않습니다. 이메일은 서버가 화면 입력에서 따로 붙여 Make로 보냅니다.

## 2. 서버에서 부르는 예

```python
from ai.diagnosis import run_diagnosis, run_more

# 진단 시작 버튼
try:
    report = run_diagnosis(store, region, menus, station)   # menus는 목록 ["칼국수", "만두"]
except Exception as e:                                       # 예상하지 못한 오류 대비
    report = {"ok": False, "error": "진단 중 오류가 났어요. 잠시 후 다시 시도해 주세요.", "problems": [str(e)[:200]]}

# 더 자세히 진단하기 버튼 (report: 화면이 보낸 1차 리포트)
report2 = run_more(report)
```

- `report["ok"]`가 false → `error`를 크게, `problems`를 목록으로 표시
- `report["more_available"]`가 true → "더 자세히 진단하기" 버튼 표시 (언급률이 높아 자동 추가 질의를 안 했거나, 자동 추가 질의가 실패한 경우). 누르면 결과가 올 때까지 버튼 비활성화
- `report2["more_error"]`가 빈 문자열이 아니면 그 문장을 버튼 아래에 표시
- 화면·메일에 꼭 표시: `report["notice"]` ("AI가 생성한 추정치입니다…", 평가기준 G7)

## 3. 배포 환경 변수 (Vercel)

| 이름 | 배포 값 | 메모 |
| --- | --- | --- |
| `GEMINI_API_KEY` | 팀 유료 키 | 저장소에 절대 올리지 않음 |
| `GEMINI_MODEL` | 실측 후 정한 모델 | 비우면 코드 기본값 (`ai/gemini_client.py` `DEFAULT_MODEL`) |
| `GEMINI_USE_SEARCH` | `1` | 무료 키는 웹 검색 할당량이 없어 `0`이어야 동작 |
| `GEMINI_REPEAT` | `3` | 시간이 부족하면 `2` |
| `GEMINI_CONCURRENCY` | `5`~`10` | 유료 키 기준. 동시 3개면 웹 검색 끔 기준 약 64초 |
| `GEMINI_TIMEOUT_SEC` | `60` | 호출 1회 시간 제한 |

- 진단 1회 최대 51회 호출, 웹 검색 켬이면 더 오래 걸림 → Vercel 함수 실행 시간 제한을 넉넉하게(최대 300초) 설정해 주세요
- 필요한 패키지: `requirements.txt` (`google-genai`, `python-dotenv`), Python 3.10 이상

## 4. 서버 없이 AI만 확인하는 방법 (프로젝트 맨 위 폴더에서)

| 확인할 것 | 명령 | 정상이면 |
| --- | --- | --- |
| 키·패키지 | `python -m ai.check_setup` | 모델 이름과 짧은 인사 답변 출력 |
| 진단 1회 + 버튼 | `python -m ai.diagnosis` | 언급률·Agent·개선 제안 출력, 언급이 많으면 버튼을 누를지 물음 |
| 같은 입력 3회 | `python -m ai.quality_check` | `docs/작업기록/품질점검.md`에 표 추가 |

- 무료 키로 시험할 때 `.env`: `GEMINI_USE_SEARCH=0`, `GEMINI_REPEAT=1`, `GEMINI_CONCURRENCY=2`
- 실행 결과 `last_diagnosis.json`은 저장소에 올리지 않습니다

## 5. 자주 나는 오류와 대처

| 화면·로그에 보이는 것 | 원인 | 대처 |
| --- | --- | --- |
| `429 RESOURCE_EXHAUSTED … exceeded your current quota` (웹 검색 켬) | 무료 키에는 웹 검색 할당량이 없음 | 유료 키로 바꾸거나 `GEMINI_USE_SEARCH=0` |
| `429 … PerMinute` | 분당 호출 한도 | 코드가 알려 준 시간만큼 기다렸다가 최대 3번 다시 시도함. 자주 나면 `GEMINI_CONCURRENCY`를 줄임 |
| `GEMINI_API_KEY가 없습니다` | `.env` 또는 Vercel 환경 변수 없음 | 키 설정. 로컬은 프로젝트 맨 위 폴더에서 실행해야 `.env`를 읽음 |
| `입력을 확인해 주세요.` | 지역에 "동"이 없음, 메뉴가 비었음 등 (AI 호출 전) | 정상 동작. 화면에 `problems` 표시 |
| `질문을 만들지 못했어요.` | 질문 생성 3번 모두 규칙 검사 실패 | 다시 시도. 반복되면 `problems` 내용을 AI 담당에게 전달 |
| `AI 답변을 받지 못했어요.` | 질의 30회가 모두 실패 (키·한도·네트워크) | `problems`의 첫 오류 메시지 확인 |
| 개선 제안이 비어 있음 | 제안 호출이 한도에 걸림 | 진단 자체는 성공. 다시 진단하면 대부분 해결 |
| Vercel에서 시간 초과 | 호출 수·웹 검색으로 300초 근접 | `GEMINI_CONCURRENCY`를 올리거나 `GEMINI_REPEAT=2` |
| `ModuleNotFoundError: google` | 패키지 미설치 | `pip install -r requirements.txt` |
| `TypeError: unsupported operand type(s) for \|` | Python 3.9 이하 | Python 3.10 이상 사용 |

## 6. 알려진 한계 (서면 자료에도 기록)

- 웹 검색을 끄면 AI가 모르는 가상 가게도 아는 척 설명할 수 있음 (10/19 행복돈까스 사례) → 배포는 웹 검색 켬
- 같은 질문에도 AI 답이 매번 달라 언급률이 회차마다 조금씩 다름 → 반복 3회 평균, 품질 점검 기록 참고
- "진단 1회당 추가 질의 1번"은 서버가 기억하지 못해 화면의 버튼 비활성화에 의존

## 7. 연락

- 10/22(목)은 AI 담당이 바로 답하기 어렵습니다. 팀 채널에 오류 메시지 전문과 입력값을 남겨 주시면 확인하는 대로 답하겠습니다.
- AI 담당이 다시 작업하는 날: 10/23(금)
