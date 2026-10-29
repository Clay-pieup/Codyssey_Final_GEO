# AI 진단 입출력 명세 (run_diagnosis · run_more)

> AI 담당 작성 · 2026-10-19 · 서버(팀장)가 AI 진단을 부를 때 쓰는 약속
> 코드: [`ai/diagnosis.py`](../../ai/diagnosis.py)의 `run_diagnosis()`, `run_more()`
> 10/20: "더 자세히 진단하기" 버튼용 `run_more()` 추가(7장), Agent 칸 실제 모양 반영(5장), 호출 수 51회로 정정, `model` 칸에 실제 모델 이름
> 실행 환경: **Python 3.10 이상** (코드에 `str | None` 문법 사용)

---

## 1. 부르는 방법

```python
from ai.diagnosis import run_diagnosis

report = run_diagnosis(
    store="행복돈까스 망원점",          # 상호 (필수)
    region="서울 마포구 망원동",         # 지역, 시·구·동 (필수)
    menus=["등심돈까스", "치즈돈까스"],  # 대표 메뉴 1~3개 (필수)
    station="망원역",                   # 가까운 역 (선택, 없으면 "")
)
# report는 dict → json.dumps(report, ensure_ascii=False)로 그대로 화면·Make에 넘기면 됨
```

- 한 번 부르면 진단이 끝날 때까지 기다렸다가 결과를 돌려줌 (동기 함수)
- 걸리는 시간: 웹 검색 끔·반복 1회 기준 약 24초 (10/19 실측). 웹 검색 켬·반복 3회는 유료 키로 측정 예정
- 호출 수: 진단 1회 최대 **51회** (질문 생성 1 + 질의 30 + 분석 10 + Agent 선택 1 + 추가 질의 6 + 추가 분석 2 + 제안 1). Agent가 실행되지 않으면 42회. 계산 근거는 [AI 활용 명세 3-1](AI_활용명세.md)
- **이메일은 받지 않음**: 이메일 수집·동의·발송은 화면·서버·Make 몫. AI 진단에는 가게 정보만 넘김 (개인정보 최소 전달)

## 2. 입력

| 이름 | 형식 | 필수 | 규칙 | 예 |
| --- | --- | :-: | --- | --- |
| `store` | 문자열 | ○ | 1~30자. 지점명 포함 가능 | `행복돈까스 망원점` |
| `region` | 문자열 | ○ | "동"까지 포함 (예: ○○동, ○○동2가) | `서울 마포구 망원동` |
| `menus` | 문자열 목록 | ○ | 1~3개 | `["등심돈까스", "치즈돈까스"]` |
| `station` | 문자열 | | 비우면 동 이름만으로 질문 생성 | `망원역` |

- 화면에서 메뉴를 쉼표로 한 칸에 받는다면 서버에서 `text.split(",")`로 목록으로 바꿔 넘기면 됨

## 3. 출력 (report)

### 3-1. 항상 들어 있는 칸

| 칸 | 형식 | 설명 |
| --- | --- | --- |
| `ok` | true/false | 진단 성공 여부 |
| `error` | 문자열 | 실패 시 사장님께 보여줄 한 줄 (성공 시 `""`) |
| `problems` | 문자열 목록 | 실패 이유 상세 (입력 오류 문장 등) |
| `input` | 객체 | 정리된 입력: `store`, `region`, `dong`(정리된 동 이름), `station`, `menus` |
| `notice` | 문자열 | "AI가 생성한 추정치…" 안내 문구 → **화면·메일에 그대로 표시** (평가기준 G7) |
| `settings` | 객체 | `use_search`, `repeat`, `concurrency` (진단 조건 기록용) |
| `model` | 문자열 | 실제 사용한 모델 이름 (예: `gemini-3.5-flash-lite`). `.env`의 `GEMINI_MODEL`, 비우면 코드 기본값 |
| `elapsed_sec` | 숫자 | 진단에 걸린 시간(초) |

### 3-2. 성공했을 때 채워지는 칸

| 칸 | 설명 |
| --- | --- |
| `questions` | 생성된 질문 10개 `[{"id": "q1", "type": "지역 일반형", "text": "망원동 맛집 추천해줘"}, …]` |
| `summary.mention` | 전체 언급률 `{"mentioned": 9, "valid": 10, "total": 10, "rate": 90}` → 화면 표시: "정상 답변 10개 중 9개 (90%)" |
| `summary.by_type` | 유형별 언급률 `{"지역 일반형": {…}, "메뉴형": {…}, "상황형": {…}, "조건형": {…}}` (각각 mention과 같은 모양) |
| `summary.rank` | `{"average": 1.3, "first_place": 5, "counted": 6}` (목록형 답변에서 평균 순위, 1위 횟수) |
| `summary.descriptions` | AI가 가게를 소개한 말 상위 3개 `[{"text": "…", "count": 2}]` |
| `summary.sentiment` | `{"긍정": 5, "중립": 3}` |
| `summary.competitors` | 함께 나온 가게 상위 3곳 `[{"name": "…", "description": "…", "answers": 8, "menu_answers": "8/9"}]` |
| `summary.sources` | 웹 검색 출처 `{"total": 131, "kinds": {"블로그": 60, "지도·리뷰": 30, "기타": 41}, "sites": [{"site": "blog.naver.com", "count": 25}, …]}` → `kinds`는 종류별 개수(블로그·지도·리뷰·언론·SNS·영상·백과·커뮤니티·기타), `sites`는 자주 나온 사이트 상위 5곳. 10/22부터 Google 중간 주소 대신 출처의 사이트 이름으로 분류 |
| `summary.low_reliability` | 정상 답변이 2/3 미만이면 true → 화면에 "결과 신뢰도 낮음" 표시 권장 |
| `answers` | 답변 원문과 분석 (질문 × 반복 수만큼). 구글 시트 `진단결과` 기록용 |
| `agent` | Agent 추가 진단 결과 (아래 5장) |
| `more_available` | true면 화면에 **"더 자세히 진단하기" 버튼** 표시. Agent 결과(`agent.trace`)가 없는 리포트면 true → 언급률이 높아 자동 추가 질의를 안 한 경우 + 자동 추가 질의가 한도 초과 등으로 실패한 경우 |
| `question_warnings` | 질문 품질 경고 목록 (예: "동 이름이 들어간 질문이 6개 미만"). 진단은 정상 진행, 화면 표시는 안 해도 됨 |
| `suggestions` | 개선 제안 3개 `[{"title": "…", "detail": "…", "evidence": "…"}]` |

`answers` 한 칸의 모양:
```json
{
  "question_id": "q3", "type": "메뉴형", "question": "망원동 치즈돈까스 맛있는 곳", "run": 1,
  "status": "ok", "text": "답변 원문…", "sources": ["https://vertexaisearch.cloud.google.com/grounding-api-redirect/…"],
  "source_sites": ["blog.naver.com"], "elapsed": 3.1, "error": "",
  "mentioned": true, "mention_check": {"code": true, "ai": true, "mismatch": false},
  "rank": 2, "description": "두툼한 등심으로 알려진 가게", "sentiment": "긍정",
  "other_stores": [{"name": "바삭공방", "description": "리뷰가 많은 돈까스집"}]
}
```
- `status`: `ok`(정상) / `failed`(호출 실패) / `empty`(빈 답변) / `refused`("정보를 찾을 수 없음") → `ok`만 언급률 분모에 들어감

### 3-3. 실패했을 때

| 상황 | `error` | `problems` 예 |
| --- | --- | --- |
| 입력 오류 (AI 호출 안 함) | `입력을 확인해 주세요.` | `["지역은 동 이름까지 입력해 주세요. (예: 서울 마포구 망원동)"]` |
| 질문 생성 실패 | `질문을 만들지 못했어요. 잠시 후 다시 시도해 주세요.` | 규칙 검사 실패 항목 |
| AI 답변을 하나도 못 받음 | `AI 답변을 받지 못했어요. 잠시 후 다시 시도해 주세요.` | 첫 번째 오류 메시지 (한도 초과 등) |

- 화면은 `ok`가 false면 `error`를 크게, `problems`를 목록으로 보여 주면 됨
- 예상하지 못한 오류에 대비해 서버에서 `try/except`로 한 번 감싸 주세요

## 4. 서버·배포 설정 (.env / Vercel 환경 변수)

| 이름 | 기본값 | 설명 |
| --- | --- | --- |
| `GEMINI_API_KEY` | (필수) | 배포 환경에는 팀 유료 키 |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | 10/22 코드 기본값 변경. 유료 키로 3.8-flash와 비교 측정 후 확정 |
| `GEMINI_USE_SEARCH` | `1` | 웹 검색 사용. 무료 키 로컬 테스트 때만 `0` |
| `GEMINI_REPEAT` | `3` | 질문마다 반복 횟수 |
| `GEMINI_CONCURRENCY` | `3` | 동시 호출 수. 유료 키는 10까지 권장 |
| `GEMINI_TIMEOUT_SEC` | `60` | 호출 1회 시간 제한 |
| `GEMINI_RATE_LIMIT_RETRIES` | `3` | 한도 초과(429) 때 기다렸다가 다시 시도하는 횟수 |
| `AGENT_THRESHOLD` | `30` | 자동 추가 질의 기준 언급률(%) |

- 필요한 패키지: 저장소 맨 위 `requirements.txt` (google-genai, python-dotenv)
- Vercel 실행 1회 300초 제한 → 웹 검색 켬·반복 3회 실측 후 `GEMINI_CONCURRENCY` 조정

## 5. Agent 칸

```json
"agent": {
  "ran": true,
  "trigger": "auto",
  "reason_to_run": "언급률 0% < 기준 30% → 추가 질의 실행",
  "trace": [
    {
      "tool": "ask_direct_name",
      "tool_label": "직접 지명형",
      "why": "멘션율이 0%로 AI가 가게를 전혀 언급하지 않아 존재 여부와 인지 상태를 확인하기 위해",
      "question": "망원동 행복돈까스 어때?",
      "args": {},
      "result": {"mentioned": 1, "valid": 3, "descriptions": ["…"], "other_stores": ["…"]},
      "answers": [ /* answers 칸과 같은 모양 */ ]
    }
  ],
  "skipped": [],
  "model": "gemini-3.5-flash-lite",
  "error": ""
}
```

| 칸 | 설명 |
| --- | --- |
| `ran` | 추가 질의를 실행했는지 |
| `trigger` | `auto`(언급률 30% 미만이라 자동) / `button`("더 자세히 진단하기") / `""`(실행 안 함) |
| `reason_to_run` | 실행한 이유 또는 안 한 이유 한 줄 → 화면에 그대로 표시 가능 |
| `trace[]` | AI가 고른 질문 도구마다 1칸 (최대 2칸). `tool_label`(질문 종류), `why`(AI가 쓴 이유), `question`, `result.mentioned`/`result.valid` |
| `trace[].tool` | `ask_direct_name`(직접 지명형) / `ask_competitor_compare`(경쟁 비교형) / `ask_situation_detail`(상황 세분형) |
| `skipped[]` | AI가 골랐지만 규칙 검사에서 뺀 질문과 이유 (예: "질문에 지역이 없음") |
| `error` | 도구 선택 실패 등 (빈 문자열이면 정상) |

- 언급률이 30% 이상이면 `{"ran": false, "trigger": "", "reason_to_run": "언급률 90% ≥ 기준 30% → 추가 질의 안 함", "trace": [], …}` + 리포트 `more_available: true`
- 자동 추가 질의가 실패하면(예: 429로 도구 선택 실패) `{"ran": true, "trace": [], "error": "…"}` + 리포트 `more_available: true` → 버튼으로 다시 시도

## 6. Make에 넘길 때 추천 필드

| Make 필드 | report에서 꺼낼 곳 |
| --- | --- |
| 상호 | `input.store` |
| 지역 | `input.region` |
| 언급률 | `summary.mention.rate` (+ `mentioned`/`valid`) |
| 유형별 결과 | `summary.by_type` |
| 추가 질의 종류 | `agent.trace[].tool_label` |
| 추가 질의 실행 방식 | `agent.trigger` (auto / button) |
| 판단 이유 | `agent.trace[].why` |
| 개선 제안 | `suggestions[].title` |
| 안내 문구 | `notice` |
| 이메일 | (report에 없음, 서버가 화면 입력에서 따로 붙임) |

## 7. "더 자세히 진단하기" 버튼 (run_more)

```python
from ai.diagnosis import run_more

report2 = run_more(report)   # report: run_diagnosis()가 돌려준 리포트를 화면이 그대로 다시 보낸 것
```

- 왜 리포트를 다시 받나: Vercel 서버는 요청마다 새로 시작해 1차 결과를 기억하지 못함 → 화면이 가진 1차 리포트(JSON)를 다시 보내면 Agent만 실행
- 버튼 표시 조건: 리포트의 `more_available`이 true일 때 (Agent 결과가 없는 리포트: 자동 추가 질의를 안 했거나 실패함)
- 하는 일: 언급률과 관계없이 Agent 실행(`agent.trigger: "button"`) → Agent 결과까지 넣어 개선 제안을 다시 만듦
- 돌려주는 값: 받은 리포트에 `agent`, `suggestions`가 새로 채워진 **리포트 전체** → 화면은 이 리포트로 그대로 다시 그리면 됨. Make 메일도 이 리포트로 보내면 추가 진단 결과까지 들어감
- 추가로 생기는 칸: `more_error`(실패 시 사장님께 보여줄 한 줄, 정상이면 `""`), `more_elapsed_sec`(버튼 실행에 걸린 시간)
- 호출 수: 최대 10회 (도구 선택 1 + 추가 질의 6 + 추가 분석 2 + 개선 제안 1), 시간은 1차 진단의 약 1/4

| 상황 | `more_error` | `more_available` |
| --- | --- | --- |
| 정상 실행 | `""` | false → 버튼 숨김 |
| 이미 추가 질의를 한 리포트 | `이미 추가 진단을 했어요. 다시 보려면 새로 진단해 주세요.` | false |
| 실패한 리포트(`ok: false`)를 보냄 | `먼저 진단을 끝까지 실행해 주세요.` | 그대로 |
| 리포트 모양이 깨짐(입력값·summary 누락) | `진단 결과가 올바르지 않아요. 새로 진단해 주세요.` | 그대로 |
| AI가 도구를 못 고름 / 모두 규칙 검사에서 빠짐 | `추가 진단을 하지 못했어요. 잠시 후 다시 눌러 주세요.` | true → 다시 누를 수 있음 |

- 진단 1회당 추가 질의 1번 원칙은 서버가 기억하지 못하므로, 화면에서 **버튼을 누르면 결과가 올 때까지 비활성화**하고 결과 리포트로 교체해 주세요 (같은 1차 리포트를 여러 번 보내는 것 방지)
- 리포트에서 `answers`(답변 원문)는 run_more에 필요 없음 → 요청 크기를 줄이려면 빼고 보내도 됨. 단, 돌려받는 리포트에도 `answers`가 빠진 채로 옴
