# AI 진단 입출력 명세 (run_diagnosis)

> AI 담당 작성 · 2026-10-19 · 서버(팀장)가 AI 진단을 부를 때 쓰는 약속
> 코드: [`ai/diagnosis.py`](../ai/diagnosis.py)의 `run_diagnosis()`

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
| `model` | 문자열 | 사용한 모델 이름 |
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
| `summary.sources` | 웹 검색 출처 `{"total": 12, "kinds": {"블로그": 7, "지도·리뷰": 5}}` |
| `summary.low_reliability` | 정상 답변이 2/3 미만이면 true → 화면에 "결과 신뢰도 낮음" 표시 권장 |
| `answers` | 답변 원문과 분석 (질문 × 반복 수만큼). 구글 시트 `진단결과` 기록용 |
| `agent` | Agent 추가 진단 `{"ran": false, "trace": []}` → **10/20 구현 후 채워짐** (아래 5장) |
| `suggestions` | 개선 제안 3개 `[{"title": "…", "detail": "…", "evidence": "…"}]` |

`answers` 한 칸의 모양:
```json
{
  "question_id": "q3", "type": "메뉴형", "question": "망원동 치즈돈까스 맛있는 곳", "run": 1,
  "status": "ok", "text": "답변 원문…", "sources": ["https://…"], "elapsed": 3.1, "error": "",
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
| `GEMINI_MODEL` | `gemini-3.8-flash` | 실측 후 확정 (3.5-flash-lite 후보) |
| `GEMINI_USE_SEARCH` | `1` | 웹 검색 사용. 무료 키 로컬 테스트 때만 `0` |
| `GEMINI_REPEAT` | `3` | 질문마다 반복 횟수 |
| `GEMINI_CONCURRENCY` | `3` | 동시 호출 수. 유료 키는 10까지 권장 |
| `GEMINI_TIMEOUT_SEC` | `60` | 호출 1회 시간 제한 |

- 필요한 패키지: 저장소 맨 위 `requirements.txt` (google-genai, python-dotenv)
- Vercel 실행 1회 300초 제한 → 웹 검색 켬·반복 3회 실측 후 `GEMINI_CONCURRENCY` 조정

## 5. Agent 칸 (10/20 구현 예정, 모양 미리 약속)

```json
"agent": {
  "ran": true,
  "reason_to_run": "전체 언급률 13% < 기준 30%",
  "trace": [
    {
      "tool": "competitor_compare",
      "tool_label": "경쟁 비교형",
      "why": "메뉴형 답변 9개 중 8개에 '바삭공방'이 나와서 경쟁 가게 대비 위치를 확인",
      "question": "망원동 돈까스집 중 어디가 나아?",
      "result": {"mentioned": 1, "valid": 3}
    }
  ]
}
```
- 언급률이 30% 이상이면 `{"ran": false, "reason_to_run": "언급률 30% 이상", "trace": []}`
- Make로 넘길 값(기획서 4-4 `진단결과` 시트): `input.store`, `input.region`, `summary.mention.rate`, `agent.trace[].tool_label`, `agent.trace[].why`

## 6. Make에 넘길 때 추천 필드

| Make 필드 | report에서 꺼낼 곳 |
| --- | --- |
| 상호 | `input.store` |
| 지역 | `input.region` |
| 언급률 | `summary.mention.rate` (+ `mentioned`/`valid`) |
| 유형별 결과 | `summary.by_type` |
| 추가 질의 종류 | `agent.trace[].tool_label` |
| 판단 이유 | `agent.trace[].why` |
| 개선 제안 | `suggestions[].title` |
| 안내 문구 | `notice` |
| 이메일 | (report에 없음, 서버가 화면 입력에서 따로 붙임) |
