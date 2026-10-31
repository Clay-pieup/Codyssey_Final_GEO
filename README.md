# Codyssey_Final_GEO

> 코디세이 AI 네이티브 Final Project · 3인 팀 · 2026-10-17 ~
>
> **처음 보시는 분은 [한눈에 보기](docs/00_한눈에보기.md)부터** (서비스·바로 써 보기·구조·현재 상태·문서 지도, 5분)

## 1. 프로젝트 개요

외식업 사장님이 상호·지역·대표 메뉴를 넣으면, 손님 질문 10개를 AI(Gemini, 웹 검색)에 3번씩 물어 **AI 답변에 우리 가게가 얼마나 나오는지(언급률)** 진단하고, 필요하면 **AI Agent**가 추가 질문을 골라 원인을 좁힌 뒤 개선 제안 3개를 화면과 메일로 전달하는 **GEO(생성형 엔진 최적화) 진단 서비스**입니다.

| 항목 | 내용 |
| --- | --- |
| 배포 URL | https://codyssey-final-geo.vercel.app/ |
| 접속 방법 | 로그인 없이 바로 사용. 가게 정보 입력 → "진단 시작하기" (약 20~35초). AI Agent 확인용 테스트 상호와 확인 순서: [기능 요구 명세서 6·7장](docs/기능요구명세서.md) |
| 테스트 계정 | 필요 없음 |
| 목표·점검 | [GOAL.md](GOAL.md) (공식 미션 목표·평가기준 G1~G7 체크리스트, 근거 링크 포함) |

## 2. 팀원 및 역할

| 역할 | 담당 업무 | 작업 브랜치 | 기여 요약 (본인 작성) | 대표 커밋·PR·문서 |
| --- | --- | --- | --- | --- |
| 팀장 | 기획·명세, 서버(백엔드), 사용자 테스트, 발표 자료(서면) 총괄, 팀원 PR 승인 | `feature/pm-backend` | 외식업 GEO 진단 주제를 제안하고, 기획서(문제 정의·타깃·AI 활용·기술 선택 근거)와 기능 요구 명세서(Must 3개·아키텍처·구현 현황)를 작성함<br>서버(api/·server/)를 설계해 화면·AI·Make를 연결하고, Vercel에 화면과 Python 함수를 한 주소로 배포함 (배포 환경 진단 20~35초 실측)<br>Gemini 유료 키(과제 전용·선불·키 분리)와 웹훅 등 비밀값을 환경 변수로 관리하고, 이메일 동의·시트 분리·파기 일정 등 개인정보 원칙을 정함<br>팀원 PR을 검토·통합하며(병합 전 빈 화면 오류 발견·수정 등) 결정 40여 건과 진행 과정을 README에 기록함<br>평가 기준표로 제출 점검표(현 GOAL.md)를 만들고, 팀 공통 Claude 규칙(CLAUDE.md)·한눈에 보기·발표 자료로 문서를 정리함 | [PR #12](https://github.com/Clay-pieup/Codyssey_Final_GEO/pull/12) (서버·배포), [PR #16](https://github.com/Clay-pieup/Codyssey_Final_GEO/pull/16) (명세서), [PR #21](https://github.com/Clay-pieup/Codyssey_Final_GEO/pull/21) (평가 대비 갱신), [기획서](docs/기획서.md), [ARCHITECTURE 6장(결정과 근거)](docs/ARCHITECTURE.md) |
| AI 담당 | 질문 생성, AI 질의·답변 분석, 개선 제안, 프롬프트 관리 | `feature/ai` | 가게 정보를 넣으면 Gemini가 얼마나 언급하는지 진단하는 AI 부분 전체를 맡음<br>Gemini 호출을 한 곳(gemini_client.py)으로 모으고, 질문 생성 → 답변 분석 → 개선 제안 3개 생성과 AI 한계 안내를 구현함<br>AI Agent: 언급이 부족한 이유를 알아보려고 질문 도구 3개(직접 지명형·경쟁 비교형·상황 세분형)를 함수로 정의하고, 진단 결과를 본 Gemini가 함수 호출로 직접 고르게 함 (G3)<br>같은 조건에서 두 모델을 재 보고(3.8-flash 진단 1회 177~191초, 3.5-flash-lite 28~32초) Vercel 300초 제한을 고려해 기본 모델을 3.5-flash-lite로 정함<br>같은 입력을 3번 돌리는 점검 스크립트(quality_check.py)를 만들어 실존 가게·가상 가게·평가자용 테스트 상호 4곳 모두 Must ①② 3회 중 3회 통과를 확인함 (G4) | [PR #10](https://github.com/Clay-pieup/Codyssey_Final_GEO/pull/10), [PR #14](https://github.com/Clay-pieup/Codyssey_Final_GEO/pull/14), [커밋 7297da3](https://github.com/Clay-pieup/Codyssey_Final_GEO/commit/7297da3), [작업기록/AI.md](docs/작업기록/AI.md), [ARCHITECTURE 6장(결정과 근거)](docs/ARCHITECTURE.md) |
| 화면·배포 담당 | 화면(프론트엔드), 외부 배포, Make 자동화 | `feature/frontend` | React와 Vite를 활용하여 GEO 진단 서비스의 사용자 입력 화면과 진단 결과 화면을 구현했습니다.<br>상호·지역·대표 메뉴를 필수 입력으로 구성하고, 가까운 역과 이메일을 선택 입력으로 처리했으며 개인정보 동의에 따른 이메일 입력 기능을 구현했습니다.<br>기본 진단 및 추가 진단 API를 프런트엔드와 연동하고, 결과 표시·로딩·오류 처리 기능을 작업했습니다.<br>Make Webhook, Google Sheets, Gmail을 연결하여 진단 결과 저장과 동의 사용자 대상 이메일 발송 자동화를 구성했습니다.<br>Make Blueprint 및 실행 증빙 자료를 GitHub에 업로드하고, 개발 과정과 해결 사항을 작업기록에 문서화했습니다. | [PR #11](https://github.com/Clay-pieup/Codyssey_Final_GEO/pull/11), [PR #17](https://github.com/Clay-pieup/Codyssey_Final_GEO/pull/17), [커밋 43d8b72](https://github.com/Clay-pieup/Codyssey_Final_GEO/commit/43d8b72) (Make 블루프린트), [커밋 6547d6a](https://github.com/Clay-pieup/Codyssey_Final_GEO/commit/6547d6a) (작업 기록)<br>※ 10/17 커밋 248f48e·210c2bc는 교육장 PC의 이전 사용자 Git 설정이 남아 다른 계정명(040611bluesky-creator)으로 기록됨. 화면·배포 담당(PuffyCripsy) 본인 작업 |

- **기여 요약은 팀원 본인이 직접 씁니다** (평가기준 G6). 3~5줄로 무엇을 했고 어떤 결정을 했는지 적어 팀장에게 전달 → 팀장이 이 표에 옮깁니다.
- 대표 커밋·PR·문서 링크는 각자 2~3개씩 고릅니다.
- 작업 규칙: 역할별 브랜치 → PR → 팀장 승인 후 `main` 병합 (저장소 룰셋으로 강제). 자세히: [협업 가이드](docs/운영/협업_가이드.md) · 팀 공통 Claude 규칙: [CLAUDE.md](CLAUDE.md)

## 3. 기술 스택과 필수 기술 요소

| 구분 | 선택 | 선택 이유 (상세: [기획서 4-3](docs/기획서.md)) |
| --- | --- | --- |
| AI | Gemini API (웹 검색, 함수 호출) | 1차는 한 AI로 끝까지 완성. 웹 검색 없이는 동네 가게를 모름 |
| 화면 | React + Vite | 화면·배포 담당 선택 |
| 서버 | Python (Vercel 함수) | AI 코드를 그대로 쓰고 키를 숨김. 화면과 한 주소로 배포 |
| 자동화 | Make | 무료 플랜으로 웹훅 → 시트 → 메일 연결 |
| 저장 | 구글 시트 (Make 기록) | 코드 없이 저장, 팀 전원 열람 |

| 필수 기술 요소 (G3) | 이 서비스에서 | 코드 위치 |
| --- | --- | --- |
| AI Agent | 질문 도구 3개(직접 지명형·경쟁 비교형·상황 세분형)를 함수로 주고, Gemini가 진단 결과를 보고 호출할 도구를 스스로 선택 | `ai/agent.py`, `ai/gemini_client.py` `choose_tools()` |
| 자동화 워크플로우 | 진단 완료 이벤트 → Make 웹훅 → 구글 시트 기록 / 의견 팝업 제출 → Make → 연락처 시트 + Gmail 리포트 발송, 의견은 Apps Script로 피드백 시트 (사람 개입 없음) | `server/make_sender.py`, [`automation/make_scenario.json`](automation/make_scenario.json) |

## 4. 문서

| 위치 | 내용 |
| --- | --- |
| `docs/` | **평가 제출물**: [한눈에 보기](docs/00_한눈에보기.md) · [기획서](docs/기획서.md) · [기능 요구 명세서](docs/기능요구명세서.md) · [사용자 피드백 기록](docs/사용자_피드백_기록.md) · [발표 자료 PDF](docs/발표자료.pdf) · [진행 기록](docs/진행기록.md) |
| `docs/` 기획 | [PRD](docs/PRD.md): 최종적으로 만들 제품의 요구사항 (멘토 과제, 팀 회의로 확정 중) |
| `docs/` 구조 | [ARCHITECTURE](docs/ARCHITECTURE.md): 구성도·흐름·측정 방법·AI 설정·약속·결정 근거를 한 장으로 |
| [`docs/운영/`](docs/운영/) | 팀 내부용: 협업 가이드, AI 실행 방법, AI 인수인계 |
| [`docs/작업기록/`](docs/작업기록/) | 담당자별 날짜순 작업 기록, 실측·품질 점검 결과 |

## 5. 실행 방법

### 5-1. 바로 써 보기
- 배포 URL https://codyssey-final-geo.vercel.app/ 접속 → 가게 정보 입력 → "진단 시작" (설치 필요 없음)

### 5-2. 구성
```
geo_frontend/   화면 (React + Vite)
api/            서버 주소 2개: /api/diagnose (진단), /api/more (더 자세히 진단하기)
server/         서버 공통 도구 (요청·응답, Make 전송)
ai/             AI 진단 (질문 생성 → 질의 → 분석 → Agent → 개선 제안)
vercel.json     배포 설정 (화면 빌드 + Python 함수 최대 300초)
```
- 흐름: 화면 → `/api/diagnose` → `ai.diagnosis.run_diagnosis()` → 결과를 화면에 응답 + Make 웹훅 → 구글 시트 기록·Gmail 발송

### 5-3. 실행 환경과 의존성
- Python 3.10 이상 (AI 코드에 `str | None` 문법 사용. Vercel 배포는 3.12)
- Node.js 20.19 이상 (화면 빌드, Vite 8 요구)
- Python 패키지: `requirements.txt` (`google-genai`, `python-dotenv`). 서버(`api/`, `server/`)는 Python 기본 도구만 사용
- 화면 패키지: `geo_frontend/package.json` (버전 고정)
- 외부 서비스: Gemini API 유료 등급 키(웹 검색 사용), Make 웹훅 주소

### 5-4. 설정값 (실제 값은 저장소에 올리지 않음)

| 이름 | 배포 값 | 설명 |
| --- | --- | --- |
| `GEMINI_API_KEY` | (비밀) | Gemini 유료 키 |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | 사용 모델 |
| `GEMINI_USE_SEARCH` | `1` | 웹 검색 사용 |
| `GEMINI_REPEAT` | `3` | 질문마다 반복 횟수 |
| `GEMINI_CONCURRENCY` | `10` | 동시 호출 수 |
| `MAKE_WEBHOOK_URL` | (비밀) | Make 웹훅 주소. 없으면 메일·시트 기록만 건너뜀 |
| `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` | (비밀) | 네이버 지역 검색(가게 검색). 없으면 검색만 "직접 입력해 주세요"로 안내 |
| `FEEDBACK_WEBHOOK_URL` | (비밀) | 사장님 의견을 피드백 시트에 기록하는 구글 Apps Script 웹 앱 주소 ([`automation/feedback_sheet.gs`](automation/feedback_sheet.gs)). 없으면 "의견 저장이 아직 준비되지 않았어요" 안내 |

- 로컬: `.env.example`을 복사해 `.env`를 만들고 값 입력 (`.env`는 `.gitignore`로 막혀 있음)
- 배포: Vercel 프로젝트 → Settings → Environment Variables

### 5-5. 직접 배포하기 (Vercel)
1. Vercel에서 이 저장소 Import (Root Directory `./`, Preset Other — 나머지는 `vercel.json`이 적용됨)
2. 5-4의 환경 변수 입력 → Deploy
3. 배포 주소 접속 → 진단 실행으로 확인

### 5-6. AI만 따로 확인하기 (서버·화면 없이)
```
pip install -r requirements.txt
python -m ai.check_setup      # 키·패키지 확인
python -m ai.diagnosis        # 진단 1회 (터미널에서 가게 정보 입력)
python -m ai.quality_check    # 같은 입력 3회 → docs/작업기록/품질점검.md
```
- 자세한 설정과 오류 대처: [AI 인수인계](docs/운영/AI_인수인계.md)
- 처음 실행하는 경우 단계별 안내: [AI 실행 방법](docs/운영/AI_실행방법.md)

## 6. 진행 기록

결정 40여 건(무엇을 골랐나 / 버린 대안 / 이유)과 날짜별 작업은 [진행 기록](docs/진행기록.md)에 있습니다. 핵심 결정만 옮기면:

| 결정 | 버린 대안 | 이유 |
| --- | --- | --- |
| Agent = 질문 도구 3개 중 AI가 함수 호출로 선택 | 질문 문장만 AI에게 받기 | "프롬프트 1회 → 응답"은 Agent로 불인정 (G3) |
| 추가 질의 여부는 규칙(언급률 30%), 무엇을 물을지는 AI | AI가 여부까지 판단 | 같은 입력이면 같은 판단 → 평가자가 확인 가능 |
| 웹 검색 사용 (유료 키, 선불·자동 충전 끔) | 무료 키, 웹 검색 끔 | 웹 검색 없이는 모르는 가게를 지어냄 (실험으로 확인) |
| 서버 = Vercel Python 함수, 요청 1번으로 완료까지 | Supabase·Tally, 단계별 요청 | AI 코드 재사용, 단순함. 실측 20~35초로 300초 제한 안 |
| 기본 모델 gemini-3.5-flash-lite | gemini-3.8-flash | 진단 1회 28~32초 vs 177~191초 |
| Must 3개(진단·Agent·자동 전달)로 묶음 | AI 단계별 8~10개 | 과정 공지 권고, Must 하나라도 실패하면 FAIL |

## 7. 결과

> 10/27 기준. 실사용자 테스트 후 갱신합니다.

**구현 (상세: [기능 요구 명세서 7장](docs/기능요구명세서.md))**
- Must ① 진단 실행 · ② AI Agent 추가 진단 · ③ 결과 자동 전달: 배포 사이트에서 동작 확인 (10/25~26)
- 같은 입력 3회 점검: 실존 가게·가상 가게·평가자용 테스트 상호 4곳 모두 Must ①② 3회 중 3회 통과 ([품질 점검 기록](docs/작업기록/품질점검.md))
- 진단 1회 약 20~35초 (Vercel 실행 제한 300초 안)

**AI Agent 실제 사례**
- 실제 동네 가게(이름 비공개): 기본 질문 30개 답변에서 언급 0회 → Agent가 "직접 지명형" 도구를 골라 가게 이름으로 질문 → 3개 중 3개 언급
- 해석: AI가 가게를 **알지만 일반 질문에는 추천하지 않는 상태** → "모르는지 / 알지만 추천 안 하는지"를 구분하는 기획 의도대로 동작 ([ARCHITECTURE 6장(결정과 근거)](docs/ARCHITECTURE.md))

**사용자 테스트**
- 진행 중: 당근 광고로 외식업 사장님 모집 (10/27~). 결과는 [사용자 피드백 기록](docs/사용자_피드백_기록.md)에 가명(T1~)으로 기록
