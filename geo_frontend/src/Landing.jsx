// ---------- 첫 화면(랜딩) 섹션들 (11/26, 위즈더플래닝 무료 진단 페이지의 "구성"을 벤치마킹) ----------
// 따라 한 것: 질문형 제목 + 버튼 2개 → 왜 지금 → 리포트 견본 → 진단 방법 → 입력 폼 → 자주 묻는 질문 → 마지막 안내
// 따라 하지 않은 것: 문구·색·로고. 글은 우리 서비스가 실제로 하는 일(Gemini 1개, 질문 10개 × 3번, Agent)에 맞춰 새로 씀
// 입력 폼은 main.jsx에 그대로 있고(id="start"), 이 파일은 그 앞뒤에 들어가는 안내 섹션만 담당
import React from "react";
import {
  ArrowRight, Bot, ChevronDown, Globe, ListChecks, MapPin, Repeat, Search,
} from "lucide-react";

// ---------- 1. 맨 위: 질문형 제목 + 버튼 2개 + 손님 질문 예시 ----------
export function LandingHero({ onStart, onSample }) {
  return (
    <section className="lp-hero">
      <div className="lp-hero-inner">
        <div className="lp-hero-copy">
          <p className="lp-eyebrow">외식업 사장님 · 무료 AI 노출 진단</p>
          <h1>손님이 AI에게 맛집을 물으면,<br /><span>우리 가게가 나올까요?</span></h1>
          <p className="lp-hero-desc">
            요즘 손님은 검색창 대신 AI에게 <b>“망원동 돈까스 맛집 추천해 줘”</b>라고 묻습니다.
            손님이 할 법한 질문 10개를 AI에게 3번씩 물어, 우리 가게가 몇 번 나오는지,
            어떻게 소개되는지, 틀린 정보는 없는지 바로 보여 드려요.
          </p>
          <div className="lp-hero-actions">
            <button type="button" className="lp-btn primary" onClick={onStart}>무료로 진단하기 <ArrowRight size={18} /></button>
            <button type="button" className="lp-btn ghost" onClick={onSample}>리포트 미리보기</button>
          </div>
          <p className="lp-hero-trust"><span>로그인 없음</span><span>보통 30초 안팎</span><span>결과는 화면에 바로</span></p>
        </div>

        {/* 손님 질문 → AI 답변 → "우리 가게는?"을 한 장으로. 가게 이름은 가상(○○·△△) */}
        <div className="lp-chat" aria-label="AI 답변 예시">
          <p className="lp-chat-label">예시 · 손님이 AI에게 물었을 때</p>
          <div className="lp-bubble user">망원동 돈까스 맛집 추천해 줘</div>
          <div className="lp-bubble ai">
            <Bot size={16} />
            <div>망원동에서 돈까스로 많이 찾는 곳이에요.<br />① <b>○○카츠</b> 두툼한 등심이 유명해요<br />② <b>△△돈까스</b> 혼밥하기 좋아요</div>
          </div>
          <div className="lp-chat-check">
            <span>우리 가게는?</span>
            <b>이번 답변엔 없어요</b>
          </div>
          <p className="lp-chat-foot">같은 질문도 AI 답이 매번 달라서, 질문 10개를 3번씩 물어 셉니다.</p>
        </div>
      </div>
    </section>
  );
}

// ---------- 2. 왜 지금: AI가 가게를 고르는 방식 (진단하며 확인한 것만) ----------
const WHY = [
  { icon: Globe, title: "웹에 적힌 글을 찾아 답해요", text: "AI는 답하기 전에 블로그·지도·리뷰 사이트를 검색해 봐요. 리포트의 ‘AI가 참고한 출처’ 카드에서 실제로 어떤 사이트를 봤는지 보여 드려요." },
  { icon: Search, title: "손님은 가게 이름 없이 물어요", text: "손님은 우리 가게 이름을 모르고 ‘동네 + 메뉴’로 물어요. 그때 AI가 우리 가게를 먼저 꺼내는지가 진짜 노출이에요." },
  { icon: Repeat, title: "같은 질문에도 답이 매번 달라요", text: "그래서 질문마다 3번씩 물어 봐요. 한 번 물어보고 ‘안 나온다’고 단정하지 않아요." },
  { icon: MapPin, title: "틀린 정보도 그대로 안내해요", text: "AI가 우리 가게 위치나 업종을 잘못 말할 수 있어요. 입력하신 동네·메뉴와 다르게 말한 정보를 찾아 표시해 드려요." },
];

export function LandingWhy() {
  return (
    <section className="lp-section">
      <p className="lp-kicker">왜 확인해야 할까요</p>
      <h2>AI는 우리 가게를 어떻게 골라서 소개할까요?</h2>
      <p className="lp-desc">AI 답변에는 순위표가 없어서, 직접 물어보기 전에는 우리 가게가 나오는지 알기 어려워요. 진단하면서 확인한 점을 정리했어요.</p>
      <div className="lp-why">
        {WHY.map(({ icon: Icon, title, text }) => (
          <article key={title}>
            <span className="lp-why-icon"><Icon size={20} /></span>
            <h3>{title}</h3>
            <p>{text}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

// ---------- 3. 리포트 미리보기: 실제 결과 화면의 카드를 작게 (숫자는 예시) ----------
export function LandingSample({ onStart }) {
  return (
    <section className="lp-section" id="sample">
      <p className="lp-kicker">리포트 미리보기</p>
      <h2>진단이 끝나면 이런 리포트를 드려요</h2>
      <p className="lp-desc">가상의 돈까스 가게를 가정한 예시예요. 숫자는 모양을 보여 드리려고 넣은 것이고 실제 측정값이 아니에요.</p>

      <div className="lp-sample">
        <article className="lp-card">
          <p className="lp-card-no">01 · AI 노출률</p>
          <strong className="lp-big">33<small>%</small><em className="warn">보통</em></strong>
          <p className="lp-card-sub">AI 답변 30개 중 10개에서 우리 가게가 나왔어요.</p>
          <div className="lp-scale"><i /><i /><i /><b style={{ left: "33%" }} /></div>
        </article>

        <article className="lp-card span2">
          <p className="lp-card-no">02 · AI가 말한 우리 가게 정보</p>
          <h3>입력한 정보와 <span className="bad">다른 내용이 1개</span> 있어요</h3>
          <ul className="lp-facts">
            <li><span>위치</span>“합정역 근처에 있는”<em className="bad">입력과 달라요</em></li>
            <li><span>영업시간</span>“매일 밤 10시까지”<em className="warn">확인해 주세요</em></li>
            <li><span>메뉴</span>“등심돈까스가 대표 메뉴”<em className="good">입력과 같아요</em></li>
          </ul>
        </article>

        <article className="lp-card">
          <p className="lp-card-no">03 · 함께 나온 가게</p>
          <h3><span className="bad">○○카츠</span>가 우리보다 2배 많이 나왔어요</h3>
          <div className="lp-bars">
            <p><span>○○카츠</span><i style={{ width: "100%" }} /><b>18</b></p>
            <p><span>△△돈까스</span><i style={{ width: "67%" }} /><b>12</b></p>
            <p className="us"><span>우리 가게</span><i style={{ width: "56%" }} /><b>10</b></p>
          </div>
        </article>

        <article className="lp-card">
          <p className="lp-card-no">04 · AI 추가 진단</p>
          <h3>가게 이름을 넣어 물으니 3번 중 3번 나왔어요</h3>
          <p className="lp-card-sub">노출률이 낮으면 AI가 추가 질문 방법을 골라 다시 물어요. 이 예시는 “AI가 가게를 알지만, 추천 목록에는 잘 올리지 않는다”는 뜻이에요.</p>
        </article>

        <article className="lp-card">
          <p className="lp-card-no">05 · 오늘 해 볼 일 3가지</p>
          <ol className="lp-todo">
            <li>지도앱 주소·소개글을 망원동 기준으로 바로잡기</li>
            <li>블로그·지도앱에 메뉴 이름을 같게 쓰기</li>
            <li>소개글에 ‘혼밥’ 같은 상황 단어 넣기</li>
          </ol>
          <p className="lp-card-sub">제안마다 진단 숫자를 근거로 달아 드려요.</p>
        </article>
      </div>

      <div className="lp-center"><button type="button" className="lp-btn primary" onClick={onStart}>우리 가게로 받아 보기 <ArrowRight size={18} /></button></div>
    </section>
  );
}

// ---------- 4. 진단 방법: 매번 같은 순서로 잰다 ----------
const STEPS = [
  { title: "손님 말투 질문 10개", text: "지역·메뉴·상황·조건 4가지로 나눠 “○○동 ○○ 맛집”처럼 만들어요. 가게 이름은 넣지 않아요." },
  { title: "AI에게 3번씩 물어요", text: "Google Gemini에 웹 검색을 켜고 질문마다 3번, 모두 30번 물어요. 답변마다 우리 가게가 나왔는지, 몇 번째인지, 어떻게 소개했는지 기록해요." },
  { title: "적게 나오면 AI Agent가 더 물어요", text: "노출률이 30%보다 낮으면 AI가 추가 질문 방법 3가지 중 알맞은 것을 골라 다시 물어요. AI가 가게를 모르는지, 알지만 추천하지 않는지 가려내요." },
  { title: "할 일 3가지를 드려요", text: "진단 숫자를 근거로 사장님이 바로 할 수 있는 일 3가지를 제안해요. 리포트는 원하시면 메일로 보관할 수 있어요." },
];

export function LandingHow() {
  return (
    <section className="lp-section lp-how-wrap">
      <p className="lp-kicker">진단 방법</p>
      <h2>모든 진단은 같은 순서로 재요</h2>
      <p className="lp-desc">같은 방법으로 재야 숫자를 믿고 비교할 수 있어요.</p>
      <ol className="lp-how">
        {STEPS.map((s, i) => (
          <li key={s.title}>
            <span className="lp-step">{i + 1}</span>
            <div><h3>{s.title}</h3><p>{s.text}</p></div>
          </li>
        ))}
      </ol>
    </section>
  );
}

// ---------- 5. 자주 묻는 질문: <details>로 펼치기 (상태 관리 없이 키보드로도 열림) ----------
const FAQ = [
  ["정말 무료인가요?", "네. 로그인이나 결제 없이 바로 쓸 수 있어요. 지금은 개발 중인 시제품이고, 진단 뒤에 유료로 바뀌는 일은 없어요."],
  ["어떤 가게가 대상인가요?", "식당·카페처럼 손님이 ‘동네 + 메뉴’로 찾는 외식업 가게예요. 지역은 ‘동’ 단위로 받아서, 읍·면 지역은 아직 진단하지 못해요."],
  ["어떤 AI에게 물어보나요?", "Google Gemini에 웹 검색을 켜고 물어요. ChatGPT나 네이버 AI는 아직 재지 않아서, 그쪽 답변과는 다를 수 있어요."],
  ["얼마나 걸리나요?", "보통 30초 안팎이에요. AI가 바쁠 때는 1~2분까지 걸릴 수 있어요."],
  ["결과는 정확한가요?", "AI가 만든 답변을 센 추정치예요. 같은 질문에도 AI 답이 매번 달라서 3번씩 물어 보지만, 다시 진단하면 숫자가 조금 달라질 수 있어요."],
  ["입력한 정보는 어떻게 되나요?", "리포트 화면은 저장되지 않아 창을 닫으면 사라져요. 서비스 개선을 위해 진단 요약(가게 이름·지역·메뉴·노출률 등)은 기록돼요. 이메일은 리포트를 메일로 받겠다고 동의하실 때만 받고, AI에는 넘기지 않아요."],
  ["노출을 올려 주나요?", "아니요. 지금 상태를 재고, 사장님이 직접 할 수 있는 일을 제안하는 데까지예요. 근거 없이 ‘노출 몇 % 상승’ 같은 약속은 하지 않아요."],
];

export function LandingFaq() {
  return (
    <section className="lp-section">
      <p className="lp-kicker">자주 묻는 질문</p>
      <h2>진단 전에 궁금하실 만한 것</h2>
      <div className="lp-faq">
        {FAQ.map(([q, a]) => (
          <details key={q}>
            <summary>{q}<ChevronDown size={18} /></summary>
            <p>{a}</p>
          </details>
        ))}
      </div>
    </section>
  );
}

// ---------- 6. 마지막 안내 ----------
export function LandingCta({ onStart }) {
  return (
    <section className="lp-cta">
      <ListChecks size={26} />
      <h2>우리 가게는 AI 답변에 몇 번 나올까요?</h2>
      <p>가게 이름만 검색하면 지역과 대표 메뉴가 자동으로 채워져요.</p>
      <button type="button" className="lp-btn primary" onClick={onStart}>무료로 진단하기 <ArrowRight size={18} /></button>
    </section>
  );
}
