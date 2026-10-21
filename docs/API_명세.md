# 화면 ↔ 서버 API 명세

> 팀장 작성 · 2026-10-21 · v0.1 (초안, 팀 확인 전)
> 10/21 결정: "더 자세히 진단하기" 후에도 메일 1통 더 발송(3장 `event: more_completed`) · 구글 시트에는 답변 원문 대신 질문별 언급 결과(`questions_text`)만 기록
> 화면(`geo_frontend/`)과 서버(`api/`)가 주고받는 약속. 서버 안에서 부르는 AI 함수는 [`AI_진단_입출력.md`](AI_진단_입출력.md) 참고
> 예시 응답 파일: [`API_예시_응답.json`](API_예시_응답.json) (가짜 AI 응답으로 만든 화면 개발용)

---

## 0. 한눈에 보기

| 화면 동작 | 서버 주소 | 서버가 하는 일 | 걸리는 시간 |
| --- | --- | --- | --- |
| "진단 시작하기" | `POST /api/diagnose` | AI 진단 1회 (`run_diagnosis`) → Make로 결과 전달 → 리포트 응답 | 1~3분 (실측 후 갱신) |
| "더 자세히 진단하기" | `POST /api/more` | Agent 추가 진단 (`run_more`) → Make로 결과 전달 → 리포트 응답 | 1차의 약 1/4 |

- 기다리는 방식: **요청 1번으로 끝까지 기다림** (10/21 결정). 화면은 응답이 올 때까지 "진단 중… 1~3분" 표시
- 화면과 서버는 같은 Vercel 프로젝트·같은 주소에 배포 → 화면에서는 주소 앞부분 없이 `/api/diagnose`로 부르면 됨
- 서버 실행 1회 최대 300초 (Vercel 설정). 넘으면 응답이 오지 않고 실패

## 1. 진단 시작: `POST /api/diagnose`

### 1-1. 화면 → 서버 (요청)

```json
{
  "store": "행복돈까스 망원점",
  "region": "서울 마포구 망원동",
  "menus": ["등심돈까스", "치즈돈까스"],
  "station": "망원역",
  "email": "owner@example.com",
  "consent": true
}
```

| 이름 | 형식 | 필수 | 규칙 |
| --- | --- | :-: | --- |
| `store` | 문자열 | ○ | 1~30자 |
| `region` | 문자열 | ○ | "동"까지 포함 |
| `menus` | 문자열 목록 | ○ | 1~3개. 화면 입력칸의 쉼표를 나눠 **목록으로** 보냄 |
| `station` | 문자열 | | 없으면 `""` |
| `email` | 문자열 | | 없으면 `""` |
| `consent` | true/false | | 개인정보 수집·이용 동의. `email`이 있으면 true여야 함 |

- 서버도 같은 규칙을 다시 검사함 (화면 검사를 거치지 않은 요청 대비)
- 이메일은 AI에 넘기지 않음. 서버가 Make로 보낼 때만 붙임 (`consent`가 true이고 형식이 맞을 때만)

### 1-2. 서버 → 화면 (응답)

- 응답 본문 = AI 리포트 전체 ([`AI_진단_입출력.md`](AI_진단_입출력.md) 3장) + 서버가 붙이는 `delivery` 칸
- 실제 모양: [`API_예시_응답.json`](API_예시_응답.json)

화면에 쓰는 칸만 추리면:

| 칸 | 화면 표시 |
| --- | --- |
| `ok` | false면 `error`를 크게, `problems`를 목록으로 |
| `summary.mention` | "정상 답변 30개 중 3개 (10%)" |
| `summary.by_type` | 질문 유형별 언급 (지역 일반형·메뉴형·상황형·조건형) |
| `summary.competitors` | 함께 나온 가게 상위 3곳과 소개 문장 |
| `summary.descriptions` | AI가 우리 가게를 소개한 말 |
| `summary.low_reliability` | true면 "결과 신뢰도 낮음" 표시 |
| `agent.reason_to_run`, `agent.trace[]` | 추가 진단: 고른 질문 종류(`tool_label`), AI가 쓴 이유(`why`), 결과(`result.mentioned`/`result.valid`) |
| `more_available` | true면 **"더 자세히 진단하기" 버튼** 표시 |
| `suggestions[]` | 개선 제안 3개 (`title`, `detail`, `evidence`) |
| `notice` | "AI가 생성한 추정치입니다…" **항상 표시** (평가기준 G7) |
| `delivery` | 메일 발송 요청 결과 (아래) |

`delivery` 칸 (서버가 붙임):

| 칸 | 뜻 |
| --- | --- |
| `requested` | 동의한 이메일이 있어 메일을 요청했는지 |
| `sent` | Make에 전달 성공 여부 (메일이 실제 도착했는지는 Make가 처리) |
| `error` | 전달 실패 이유. 진단 결과는 그대로 보여 주고, "메일 발송에 실패했어요" 정도만 표시 |

### 1-3. HTTP 상태

| 상태 | 언제 | 응답 본문 |
| --- | --- | --- |
| 200 | 진단 성공 **또는** 입력 오류·AI 실패 | 리포트 (`ok`로 구분) |
| 400 | 요청이 JSON이 아니거나 모양이 틀림 | `{"ok": false, "error": "요청 형식이 올바르지 않아요.", "problems": [...]}` |
| 405 | `POST`가 아닌 방식 | `{"ok": false, "error": "POST로 요청해 주세요."}` |
| 500 | 서버 안에서 예상 못 한 오류 | `{"ok": false, "error": "진단 중 오류가 났어요. 잠시 후 다시 시도해 주세요."}` |
| (응답 없음) | 300초 초과 등 | 화면이 "시간이 오래 걸려 실패했어요. 다시 시도해 주세요." 표시 |

- 입력 오류도 200으로 돌려주는 이유: 화면이 `ok`·`error`·`problems` 한 가지 모양만 처리하면 되도록

## 2. 더 자세히 진단하기: `POST /api/more`

### 2-1. 요청

```json
{
  "report": { "...": "/api/diagnose에서 받은 리포트 그대로" },
  "email": "owner@example.com",
  "consent": true
}
```

- 서버는 1차 진단을 기억하지 못함 → 화면이 가진 리포트를 그대로 다시 보냄
- `report.answers`(답변 원문)는 빼고 보내도 됨 (요청이 가벼워짐). 빼면 돌려받는 리포트에도 없음
- 버튼을 누르면 응답이 올 때까지 **버튼 비활성화** (같은 리포트로 여러 번 실행 방지)

### 2-2. 응답

- `agent`, `suggestions`가 새로 채워진 리포트 전체 + `more_error`, `more_elapsed_sec`, `delivery`
- `more_error`가 `""`가 아니면 버튼 아래에 그 문장 표시 ([`AI_진단_입출력.md`](AI_진단_입출력.md) 7장 표)
- 화면은 받은 리포트로 결과 화면을 다시 그림

## 3. 서버 → Make (웹훅)

- 진단이 끝나면 서버가 Make 웹훅 주소로 결과를 보냄 → Make가 구글 시트 기록 + (이메일이 있으면) Gmail 발송
- 웹훅 주소는 비밀값 → Vercel 환경 변수 `MAKE_WEBHOOK_URL`에만 저장, 저장소에 올리지 않음
- Make에서 칸을 클릭으로 연결하기 쉽게 **모든 값을 한 단계짜리 글자·숫자로** 보냄 (목록·객체 없음)
- 보내기 실패해도 진단 결과는 화면에 그대로 응답 (`delivery.error`에 기록)

| 칸 | 예 | 시트 `진단결과` | 시트 `연락처` | 메일 |
| --- | --- | :-: | :-: | :-: |
| `event` | `diagnosis_completed` / `more_completed` | ○ | | |
| `diagnosed_at` | `2026-10-21 15:30` (한국 시각) | ○ | ○ | |
| `store` | 행복돈까스 망원점 | ○ | | ○ |
| `region` | 서울 마포구 망원동 | ○ | | ○ |
| `station` | 망원역 | ○ | | |
| `menus` | 등심돈까스, 치즈돈까스 | ○ | | |
| `mention_rate` | 10 | ○ | | ○ |
| `mention_text` | 정상 답변 30개 중 3개 (10%) | ○ | | ○ |
| `by_type_text` | 지역 일반형 0/6 · 메뉴형 0/9 · 상황형 3/9 · 조건형 0/6 | ○ | | ○ |
| `competitors_text` | 바삭공방 | ○ | | ○ |
| `questions_text` | `q1 망원동 점심 맛집 추천해줘 → 0/3` (질문 10줄) | ○ | | |
| `agent_trigger` | auto / button / (빈칸) | ○ | | |
| `agent_text` | 경쟁 비교형: 망원동 돈까스집 중 어디가 나아? → 0/3 (이유: …) | ○ | | ○ |
| `suggestions_text` | 1. 제목 - 할 일 (근거) (3줄) | ○ | | ○ |
| `notice` | AI가 생성한 추정치입니다… | | | ○ |
| `low_reliability` | true / false | ○ | | ○ |
| `model` | gemini-3.5-flash-lite | ○ | | |
| `email` | owner@example.com (동의했을 때만, 아니면 빈칸) | | ○ | 받는 사람 |
| `consent` | true / false | | ○ | |

- `진단결과` 시트에는 이메일을 넣지 않음 (기획서 4-4: 시트 분리, `연락처`는 2026-11-24 파기)
- Make 시나리오: 웹훅 → 시트 `진단결과` 기록 → (`email`이 있으면) 시트 `연락처` 기록 + Gmail 발송

## 4. 서버 환경 변수 (Vercel)

| 이름 | 값 | 비고 |
| --- | --- | --- |
| `GEMINI_API_KEY` | 배포용 유료 키 | 팀장만 입력 |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | 10/21 결정 |
| `GEMINI_USE_SEARCH` | `1` | |
| `GEMINI_REPEAT` | `3` | 300초에 가까우면 `2` |
| `GEMINI_CONCURRENCY` | `10` | 유료 키 기준 |
| `MAKE_WEBHOOK_URL` | Make 웹훅 주소 | 화면·배포 담당이 Make에서 만든 주소를 팀장에게 개인 메시지로 전달 |

## 5. 로컬에서 화면 개발할 때

- 서버 없이 화면을 만들 때는 [`API_예시_응답.json`](API_예시_응답.json)을 응답으로 쓰면 됨 (가짜 데이터, 실제 진단 아님)
- 배포 후에는 배포 주소에서 실제 서버로 확인

## 6. 남은 위험

- 서버 주소는 누구나 부를 수 있음 → 반복 요청 시 비용 발생. Gemini 선불 충전·자동 충전 끔으로 최대 손해를 충전액으로 제한
- 웹 검색 켬·반복 3회의 실제 시간은 유료 키 측정 전 → 300초에 가까우면 `GEMINI_REPEAT=2`
