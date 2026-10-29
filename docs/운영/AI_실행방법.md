# AI 진단 실행 방법 (서버·화면 없이)

> AI 담당 작성 · 2026-10-23 · README 7-6 "AI만 따로 확인하기"의 자세한 안내
> 처음 보는 사람이 내 컴퓨터에서 AI 진단을 직접 돌려 보고, Must ① 진단 실행·② AI Agent 추가 진단을 확인하는 순서입니다.
> 배포된 서비스를 써 보기만 하려면 설치가 필요 없습니다 → https://codyssey-final-geo.vercel.app/

---

## 0. 한눈에 보기

| 단계 | 할 일 | 명령 | 성공 기준 | 시간 |
| :-: | --- | --- | --- | :-: |
| 1 | 준비물 확인 | `python --version` | 3.10 이상 | 1분 |
| 2 | 받기·설치 | `git clone …` → `pip install -r requirements.txt` | `Successfully installed google-genai …` | 3분 |
| 3 | 키 설정 | `copy .env.example .env` → 메모장 | `.env`에 키 저장 | 2분 |
| 4 | 준비 확인 | `python -m ai.check_setup` | `OK` 세 줄 | 10초 |
| 5 | Must ① + 버튼 | `python -m ai.diagnosis` → 명동교자 → `y` | 언급률·개선 제안 3개 + 버튼 Agent | 1~2분 |
| 6 | Must ② 자동 | `python -m ai.diagnosis` → 초록별돈까스 망원점 | 언급률 0% → 자동 Agent | 1~2분 |
| 7 | 3회 점검 (선택) | `python -m ai.quality_check` → `3` | `3/3회 통과 → 기준 충족` | 2~6분 |
| 8 | 정리 | `Remove-Item .env` | `.env` 없음 | 10초 |

진단 한 번에 안에서 일어나는 일 (기다리는 동안 화면에 아무것도 안 나오는 이유):

```
입력 확인 → 질문 10개 생성 (Gemini 1회) → 질문마다 3회 질의 (30회, 동시에)
→ 답변 분석 (10회) → 언급률 집계 → [언급률 < 30%] Agent: 도구 선택 1회 + 추가 질의 최대 6회 + 분석 2회
→ 개선 제안 (1회) → 결과 출력
```
- 진단 1회 Gemini 호출: 최대 51회 (Agent 없으면 42회). 반복 1회로 줄이면 약 1/3

## 1. 준비물

| 준비물 | 확인 방법 | 메모 |
| --- | --- | --- |
| Python 3.10 이상 | `python --version` (Windows에서 안 되면 `py --version`) | 코드에 `str \| None` 문법을 써서 3.9 이하는 실행 안 됨 |
| git | `git --version` | 저장소 받기용 |
| Gemini API 키 | [Google AI Studio](https://aistudio.google.com/)에서 발급 | 아래 표 참고 |

| 키 종류 | 할 수 있는 것 | 설정 |
| --- | --- | --- |
| 무료 키 | 진단 흐름·Agent 동작 확인 (웹 검색 없이) | `GEMINI_USE_SEARCH=0` 필수. 무료 키에는 웹 검색 할당량이 없어 켜면 모든 질의가 429 오류 |
| 유료 키 | 배포와 같은 조건 (웹 검색 켬) | 결제가 연결된 프로젝트에서 만든 키여야 함 |

- 키는 `.env` 파일에만 넣고, 저장소·채팅·스크린샷에 남기지 않습니다

## 2. 받기와 설치

Windows PowerShell 기준입니다. Mac·Linux는 아래 표처럼 바꿔 쓰면 됩니다.

| 하는 일 | Windows (PowerShell) | Mac·Linux (터미널) |
| --- | --- | --- |
| Python 실행 | `python` (안 되면 `py`) | `python3` |
| 패키지 설치 | `pip install -r requirements.txt` | `python3 -m pip install -r requirements.txt` |
| `.env` 만들기 | `copy .env.example .env` | `cp .env.example .env` |
| `.env` 편집 | `notepad .env` | `nano .env` 또는 편집기로 열기 |
| `.env` 삭제 | `Remove-Item .env` | `rm .env` |

```powershell
git clone https://github.com/Clay-pieup/Codyssey_Final_GEO.git
cd Codyssey_Final_GEO
pip install -r requirements.txt
```

- `pip`를 못 찾으면: `py -m pip install -r requirements.txt`
- 설치되는 패키지: `google-genai`, `python-dotenv` (두 개뿐)
- 이후 모든 명령은 **이 폴더(프로젝트 맨 위)** 에서 실행합니다. 다른 폴더에서 실행하면 `.env`를 못 읽습니다

## 3. 설정 (.env)

```powershell
copy .env.example .env
notepad .env
```

메모장에서 아래처럼 채우고 저장합니다. 비워 둔 칸은 코드 기본값을 씁니다.

무료 키로 시험할 때 `.env` 예시 (`=` 앞뒤에 빈칸·따옴표 없이):
```
GEMINI_API_KEY=여기에_본인_키
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_USE_SEARCH=0
GEMINI_REPEAT=1
GEMINI_CONCURRENCY=2
```

변수별 설명:

| 이름 | 무료 키로 시험 | 유료 키 (배포와 같음) | 설명 |
| --- | --- | --- | --- |
| `GEMINI_API_KEY` | 본인 키 | 유료 키 | 필수 |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | 이름 앞에 `gemini-`를 꼭 붙임. 비우면 같은 모델 |
| `GEMINI_USE_SEARCH` | `0` | `1` | 웹 검색 사용 |
| `GEMINI_REPEAT` | `1` | `3` | 질문마다 반복 횟수 (1이면 호출이 1/3) |
| `GEMINI_CONCURRENCY` | `2` | `10` | 동시 호출 수 (무료 키는 분당 15회 한도라 낮게) |
| `GEMINI_TIMEOUT_SEC` | (비움, 60) | (비움, 60) | 호출 1회 시간 제한(초) |
| `GEMINI_RATE_LIMIT_RETRIES` | (비움, 3) | (비움, 3) | 분당 한도(429) 때 기다렸다가 다시 시도하는 횟수 |
| `AGENT_THRESHOLD` | (비움, 30) | (비움, 30) | 자동 Agent 기준 언급률(%) |
| `MAKE_WEBHOOK_URL` | (비움) | (비움) | 서버용. AI만 시험할 때는 필요 없음 |

- 키가 제대로 읽히는지 키를 화면에 보이지 않게 확인하는 방법 (끝 4자리만 출력):
```powershell
python -c "import os; from dotenv import load_dotenv; load_dotenv(); k=os.getenv('GEMINI_API_KEY',''); print(len(k), k[-4:])"
```

## 4. 확인 순서

### 4-1. 준비 확인 `ai.check_setup` (10초)

```powershell
python -m ai.check_setup
```

정상이면 세 줄이 나옵니다.
```
1) 패키지 확인
   OK: google-genai, python-dotenv 설치됨
2) 프롬프트 파일 확인
   OK: question_generation.md 읽음 (…자, 빈칸 채우기 성공)
3) Gemini 호출 확인
   OK: gemini / gemini-3.5-flash-lite, …초 걸림 → 답변: …
```
- 3번이 "건너뜀"이면 `.env`에 키가 없는 것, "실패"면 키나 모델 이름을 확인

### 4-2. Must ① 진단 실행 + 버튼 `ai.diagnosis` (무료 키 1~2분, 유료 키 30초 안팎)

```powershell
python -m ai.diagnosis
```

입력 예 (실존 가게, 언급이 많은 경우):
```
상호: 명동교자
지역 (시·구·동): 서울 중구 명동
가까운 역 (없으면 Enter):
대표 메뉴 1~3개, 쉼표로 구분: 칼국수, 만두
```

출력에서 확인할 것:

| 출력 줄 | 뜻 |
| --- | --- |
| `[언급률] 정상 답변 30개 중 27개 (90%)` | 손님 질문 답변 중 가게가 나온 비율 (분모는 정상 답변만) |
| `지역 일반형: 6/6`, `메뉴형: …` | 질문 유형별 언급 |
| `[순위]`, `[AI가 소개하는 말]`, `[함께 나온 가게]` | 목록형 답변에서의 순위, 가게 묘사, 경쟁 가게 |
| `[Agent] 언급률 90% ≥ 기준 30% → 추가 질의 안 함` | 언급이 많아 자동 Agent는 실행 안 됨 |
| `[개선 제안]` 3개 | 진단 결과를 근거로 한 제안 |
| `'더 자세히 진단하기' 버튼을 눌러 볼까요? (y/N)` | **`y` 입력** → Must ② 버튼 경로 확인 |

`y`를 누른 뒤:
```
[더 자세히 진단하기] 12.4초

[Agent] 사장님이 '더 자세히 진단하기'를 눌러 실행 (언급률 90%)
  - 상황 세분형: "명동 혼밥 점심 어디가 좋아?" → 언급 2/3
    고른 이유: 상황형 3개 중 2개만 언급되어 …
```
- 질문과 이유는 AI가 매번 새로 고르므로 위 문장과 다를 수 있습니다
- 전체 결과는 `last_diagnosis.json`에 저장됩니다 (저장소에는 올리지 않음)

### 4-3. Must ② 자동 Agent `ai.diagnosis` (평가자용 테스트 상호)

실존하지 않는 상호를 넣으면 AI가 모르는 가게라 언급률이 0%가 되어 Agent가 자동으로 실행됩니다.

```
상호: 초록별돈까스 망원점
지역 (시·구·동): 서울 마포구 망원동
가까운 역 (없으면 Enter):
대표 메뉴 1~3개, 쉼표로 구분: 등심돈까스
```

기대 결과:
```
[언급률] 정상 답변 30개 중 0개 (0%)
[Agent] 언급률 0% < 기준 30% → 추가 질의 실행
  - 직접 지명형: "망원동 초록별돈까스 어때?" → 언급 0/3
    고른 이유: 언급률이 0%로 AI가 가게를 아예 모르는지 확인하기 위해 …
```
- 다른 테스트 상호: "달무리칼국수 명동점" / "서울 중구 명동" / "칼국수"
- 웹 검색을 끈 무료 키에서는 AI가 모르는 가게를 아는 척 설명할 수 있습니다 (알려진 한계). 배포와 같은 결과는 유료 키 + 웹 검색 켬에서 확인

### 4-4. 같은 입력 3회 점검 `ai.quality_check` (G4)

```powershell
python -m ai.quality_check
```

```
  1. 명동교자 (언급 많음 → 버튼으로 Agent 확인)
  2. 가상 가게 (언급 0% → 자동 Agent 확인)
  3. 평가자용 후보 A: 초록별돈까스 망원점
  4. 평가자용 후보 B: 달무리칼국수 명동점
  5. 직접 입력
번호: 3
```

- 같은 입력으로 진단을 3번 돌리고, 회차마다 Must ①(성공·질문 10개·언급률·개선 제안 3개)과 Must ②(고른 질문 종류와 이유)를 판정
- 마지막에 `Must ① 진단 실행 3/3회 통과 → 기준 충족` 같은 줄과 표가 나오고, `docs/작업기록/품질점검.md` 맨 아래에 자동으로 덧붙음
- 지금까지의 결과: 4곳 모두 3회 중 3회 통과 ([품질점검.md](../작업기록/품질점검.md))

결과 표 읽는 법 (10/22 실제 결과 일부):
```
- 설정: 모델 gemini-3.5-flash-lite · 웹 검색 켬 · 반복 3회 · 동시 10개
- **Must ① 진단 실행 3/3회 통과 → 기준 충족**
- **Must ② AI Agent 추가 진단 3/3회 통과 → 기준 충족**

| 회차 | 언급(정상 답변 중) | Agent | 고른 질문 종류 | 제안 | 질문 경고 | 시간(초) | Must ① | Must ② |
| 1 | 0/30 (0%) | 자동 | 직접 지명형 | 3 | 0 | 30.6 | 통과 | 통과 |
```

| 칸 | 뜻 |
| --- | --- |
| Agent | `자동`(언급률 30% 미만), `버튼`(자동 결과가 없어 `run_more` 실행), `안 함` |
| 질문 경고 | "역 입력 시 동 이름 6개 이상" 같은 되도록 지킬 규칙을 어긴 수 (진단은 계속함) |
| Must ①·② | `통과` 또는 못 맞춘 이유 (예: "진단 실패: 질문을 만들지 못했어요 (모델 '…'을 찾을 수 없어요)") |

### 4-5. 모델·웹 검색 비교 `ai.measure` (선택)

```powershell
python -m ai.measure
```

- 상호·동·대표 메뉴를 입력 (여러 곳 가능, 상호를 비우고 Enter → 종료)
- 고정 질문 3개 × 웹 검색 끔/켬 × 2회 = 가게 1곳당 12회 호출 → 호출 시간·언급 여부·출처 사이트를 `docs/작업기록/실측결과.md`에 기록
- 두 모델을 비교하려면 `.env`의 `GEMINI_MODEL`만 바꿔서 두 번 실행

### 4-6. 결과 파일 읽는 법 `last_diagnosis.json`

`ai.diagnosis`가 끝나면 전체 리포트가 이 파일에 저장됩니다. 서버가 화면에 돌려주는 것과 같은 모양입니다.

| 칸 | 예 | 뜻 |
| --- | --- | --- |
| `ok` | `true` | 진단 성공 여부. `false`면 `error`, `problems`에 이유 |
| `model` | `"gemini-3.5-flash-lite"` | 실제 사용한 모델 |
| `questions` | `[{"id": "q1", "type": "지역 일반형", "text": "명동 점심 맛집 추천해줘"}, …]` | 생성된 질문 10개 |
| `summary.mention` | `{"mentioned": 27, "valid": 30, "rate": 90}` | 언급률과 분모 |
| `summary.by_type` | `{"메뉴형": {"mentioned": 8, "valid": 9, …}, …}` | 유형별 언급 |
| `summary.sources` | `{"total": 152, "kinds": {"블로그": 57, …}, "sites": […]}` | 출처 종류와 자주 나온 사이트 (웹 검색 켰을 때) |
| `agent.trigger` | `"auto"` / `"button"` / `""` | Agent 실행 방식 |
| `agent.trace[]` | `tool_label`, `why`, `question`, `result` | AI가 고른 질문 종류·이유·결과 |
| `more_available` | `true` | 화면에 "더 자세히 진단하기" 버튼을 보여 줄지 |
| `suggestions[]` | `title`, `detail`, `evidence` | 개선 제안 3개와 근거 |
| `notice` | `"AI가 생성한 추정치입니다…"` | 화면·메일에 표시할 안내 문구 |

- 전체 칸 설명: [AI 진단 입출력](../기술/AI_진단_입출력.md)

### 4-7. 배포된 서버에 직접 요청해 보기 (설치 없이, 선택)

화면을 거치지 않고 배포 서버의 AI 진단을 직접 확인하는 방법입니다. 팀 유료 키로 진단 1회(Gemini 약 40회)가 실행됩니다.

1. 크롬·엣지에서 https://codyssey-final-geo.vercel.app/ 열기
2. `F12` → **Console** 탭
3. 붙여 넣기가 막히면 `allow pasting`을 직접 입력하고 Enter
4. 아래 코드를 붙여 넣고 Enter → 20~30초 뒤 결과 세 줄

```javascript
fetch('/api/diagnose',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({store:'명동교자',region:'서울 중구 명동',menus:['칼국수','만두'],station:''})}).then(r=>r.json()).then(j=>{console.log('모델', j.model, '/', j.elapsed_sec+'초', '/ 언급률', j.summary?.mention?.rate+'%'); console.log('출처', JSON.stringify(j.summary?.sources)); console.log('첫 답변 사이트', JSON.stringify(j.answers?.[0]?.source_sites));})
```

10/23 실제 결과:
```
모델 gemini-3.5-flash-lite / 19.3초 / 언급률 76%
출처 {"total":152,"kinds":{"기타":30,"블로그":57,"SNS·영상":36,"지도·리뷰":16,"언론":7,"백과·커뮤니티":6},"sites":[{"site":"tistory.com","count":57}, …]}
```
- 이 코드는 우리 서버의 `/api/diagnose`에 진단을 요청하고 결과 일부만 출력합니다. 다른 곳으로 데이터를 보내지 않습니다

## 5. 걸리는 시간 (참고)

| 조건 | 진단 1회 |
| --- | :-: |
| 유료 키 · 웹 검색 켬 · 반복 3회 · 동시 10개 · 3.5-flash-lite | 28~32초 (배포 환경 19~23초) |
| 무료 키 · 웹 검색 끔 · 반복 1회 · 동시 2개 · 3.5-flash-lite | 70~120초 (분당 한도 대기 포함) |
| 유료 키 · 같은 조건 · 3.8-flash | 177~191초 (느려서 기본 모델에서 제외) |

- 1분이 넘게 아무것도 안 나와도 멈춘 게 아닙니다. 진단이 끝나야 결과가 한꺼번에 나옵니다
- 3분이 넘으면 `.env`의 모델 이름을 확인하세요

## 6. 자주 나는 문제

| 화면에 보이는 것 | 원인 | 해결 |
| --- | --- | --- |
| `Python was not found` (Microsoft Store 안내) | `python` 명령이 연결 안 됨 | `py -m ai.diagnosis`처럼 `py`로 실행 |
| `ModuleNotFoundError: No module named 'google'` | 패키지 미설치 | `pip install -r requirements.txt` |
| `GEMINI_API_KEY가 없습니다` | `.env`가 없거나 다른 폴더에서 실행 | 프로젝트 맨 위 폴더에서 실행, `.env` 저장 확인 |
| 모든 질의가 `429 … exceeded your current quota` | 무료 키로 웹 검색을 켬 | `GEMINI_USE_SEARCH=0` 또는 유료 키 |
| `질문을 만들지 못했어요` + "모델 '…'을 찾을 수 없어요" | 모델 이름 오류 (`gemini-` 빠짐 등) | `GEMINI_MODEL=gemini-3.5-flash-lite` |
| `입력을 확인해 주세요` + "지역은 동 이름까지…" | 지역에 동이 없음 (예: "망원점") | "서울 마포구 망원동"처럼 동까지 입력 |
| `Direct use of automatic function calling (AFC)…` | Gemini SDK 안내 문구 | 결과와 무관, 무시 |
| `TypeError: unsupported operand type(s) for \|` | Python 3.9 이하 | Python 3.10 이상 사용 |

- 그 밖의 오류와 서버 연결: [AI 인수인계](AI_인수인계.md) 8장

## 7. 끝난 뒤

- 공용 컴퓨터라면 키 파일 삭제: `Remove-Item .env` (Mac·Linux: `rm .env`)
- `last_diagnosis.json`은 실행 결과라 저장소에 올리지 않습니다
- `품질점검.md`·`실측결과.md`에 덧붙은 기록을 남길지는 필요에 따라 결정 (시험 실행이면 `git checkout -- docs/작업기록/품질점검.md`로 되돌림)
