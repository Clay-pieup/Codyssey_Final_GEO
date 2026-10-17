# 답변 분석 프롬프트

- 버전: v1 (2026-10-17)
- 근거: docs/질문세트_측정기준.md 5·6장
- 빈칸: $store_name, $dong, $question, $answer
- 설정: temperature 0, JSON 출력
- 이 줄 아래 `---` 다음부터 AI에 보내짐

---
[할 일]
아래는 손님 질문에 대한 AI 챗봇의 답변이다.
이 답변에 "$store_name"($dong)이 나오는지 분석해서 JSON으로만 답하라.

[판정 규칙]
- 띄어쓰기, 돈가스/돈까스 표기, 지점명이 달라도 같은 가게면 언급으로 본다
- 다른 지역의 같은 이름 가게는 언급이 아니다
- "행복한 돈까스"처럼 상호가 아닌 일반 표현은 언급이 아니다
- 출처 링크가 아니라 본문 기준으로 판단한다

[추출할 것]
- mentioned: 언급 여부 (true/false)
- is_list: 답변이 여러 가게를 나열하는 형태인지 (true/false)
- rank: 나열 형태일 때 이 가게가 처음 나온 순서 (1부터, 아니면 null)
- description: 이 가게를 설명한 문구 원문 (50자 이내, 없으면 null)
- sentiment: "긍정" / "중립" / "부정" (언급 없으면 null)
- other_stores: 답변에 나온 다른 가게 목록 [{"name": "...", "description": "..."}]

[출력 형식]
{"mentioned": true, "is_list": true, "rank": 2, "description": "...", "sentiment": "긍정", "other_stores": [{"name": "...", "description": "..."}]}

[질문]
$question

[답변]
$answer
