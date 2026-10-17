import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowRight, BarChart3, Bot, CheckCircle2, ChevronRight, CircleHelp,
  ClipboardCheck, Compass, Mail, MapPin, Search, ShieldCheck, Store,
  Utensils, WandSparkles
} from "lucide-react";
import "./styles.css";

function App() {
  const [form, setForm] = useState({
    storeName: "", region: "", menu: "", email: "", consent: false
  });
  const [showResult, setShowResult] = useState(false);
  const [error, setError] = useState("");
  const [showHelp, setShowHelp] = useState(false);

  const update = (key, value) => {
    setForm((old) => ({ ...old, [key]: value }));
    setError("");
  };

  const startDiagnosis = (event) => {
    event.preventDefault();
    if (!form.storeName.trim() || !form.region.trim() || !form.menu.trim() || !form.email.trim()) {
      setError("상호, 지역, 대표 메뉴, 이메일을 모두 입력해 주세요.");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      setError("이메일 주소를 확인해 주세요.");
      return;
    }
    if (!form.consent) {
      setError("결과 발송을 위한 개인정보 수집·이용에 동의해 주세요.");
      return;
    }
    setShowResult(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const reset = () => {
    setShowResult(false);
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#" onClick={(e) => { e.preventDefault(); reset(); }}>
          <span className="brand-mark"><Compass size={21} /></span>
          <span>geo<span className="brand-dot">.</span>check</span>
        </a>
        <div className="topbar-right">
          <span className="status-dot" /> 외식업 매장 AI 노출 진단
          <button className="icon-button" aria-label="서비스 안내" onClick={() => setShowHelp(!showHelp)}>
            <CircleHelp size={19} />
          </button>
        </div>
      </header>

      {showHelp && (
        <div className="help-banner">
          이 서비스는 대화형 AI 답변에서 우리 가게가 어떻게 언급되는지 점검하는 도구입니다.
          현재 화면은 개발 중인 시제품입니다. <button onClick={() => setShowHelp(false)}>닫기</button>
        </div>
      )}

      {!showResult ? (
        <>
          <main>
            <section className="hero">
              <div className="hero-copy">
                <div className="eyebrow"><WandSparkles size={15} /> GENERATIVE ENGINE OPTIMIZATION</div>
                <h1>AI가 우리 가게를<br /><span>추천하고 있을까요?</span></h1>
                <p className="hero-desc">
                  가게 정보를 입력하면 AI 검색 답변에서의 브랜드 노출을 진단하고,
                  더 잘 발견되기 위한 개선 방향을 확인할 수 있습니다.
                </p>
                <div className="hero-points">
                  <span><CheckCircle2 size={16} /> AI 답변 언급 확인</span>
                  <span><CheckCircle2 size={16} /> 주변 경쟁 가게 비교</span>
                  <span><CheckCircle2 size={16} /> 실행 가능한 개선 제안</span>
                </div>
              </div>
              <div className="hero-visual" aria-hidden="true">
                <div className="orbit orbit-one" />
                <div className="orbit orbit-two" />
                <div className="visual-card visual-main">
                  <div className="visual-icon"><Bot size={27} /></div>
                  <div>
                    <div className="visual-label">AI DISCOVERY</div>
                    <strong>우리 가게는 발견되고 있나요?</strong>
                  </div>
                </div>
                <div className="floating-card floating-top"><Search size={17} /><span>동네 맛집 검색</span><span className="mini-check">✓</span></div>
                <div className="floating-card floating-bottom"><BarChart3 size={18} /><span>브랜드 노출 진단</span><span className="mini-bars"><i /><i /><i /><i /></span></div>
                <div className="visual-spark spark-a">✦</div><div className="visual-spark spark-b">✧</div>
              </div>
            </section>

            <section className="content-grid">
              <div className="intro-column">
                <div className="section-kicker">START YOUR CHECKUP</div>
                <h2>우리 가게 정보 입력</h2>
                <p className="section-desc">아래 네 가지 정보를 입력해 주세요.<br />진단 결과는 입력하신 이메일로 보내드릴 예정입니다.</p>
                <div className="privacy-note">
                  <ShieldCheck size={20} />
                  <div><strong>정보는 안전하게 관리합니다</strong><p>이메일은 결과 발송 목적으로만 사용하며, 동의 여부를 확인한 후 처리합니다.</p></div>
                </div>
                <div className="steps">
                  <div className="step-item"><span className="step-number">01</span><div><strong>매장 정보 입력</strong><p>상호 · 지역 · 대표 메뉴</p></div></div>
                  <div className="step-item"><span className="step-number">02</span><div><strong>AI 답변 노출 진단</strong><p>질문별 언급 여부와 경쟁 상황 분석</p></div></div>
                  <div className="step-item"><span className="step-number">03</span><div><strong>개선 제안 확인</strong><p>매장 홍보에 적용할 다음 행동 확인</p></div></div>
                </div>
              </div>

              <form className="form-card" onSubmit={startDiagnosis} noValidate>
                <div className="form-heading">
                  <div><span className="form-step">STEP 01</span><h3>매장 기본 정보</h3></div>
                  <span className="required-note">* 필수 입력</span>
                </div>
                <label htmlFor="storeName">가게 이름 <span>*</span></label>
                <div className="input-wrap"><Store size={18} /><input id="storeName" value={form.storeName} onChange={(e) => update("storeName", e.target.value)} placeholder="예: 소담 돈가스" maxLength={80} /></div>

                <label htmlFor="region">지역 <span>*</span></label>
                <div className="input-wrap"><MapPin size={18} /><input id="region" value={form.region} onChange={(e) => update("region", e.target.value)} placeholder="예: 창원시 성산구 상남동" maxLength={100} /></div>

                <label htmlFor="menu">대표 메뉴 <span>*</span></label>
                <div className="input-wrap"><Utensils size={18} /><input id="menu" value={form.menu} onChange={(e) => update("menu", e.target.value)} placeholder="예: 돈가스, 냉모밀, 카레" maxLength={150} /></div>
                <p className="field-help">메뉴는 쉼표로 구분해 여러 개 입력할 수 있습니다.</p>

                <div className="form-divider" />
                <label htmlFor="email">결과 받을 이메일 <span>*</span></label>
                <div className="input-wrap"><Mail size={18} /><input id="email" type="email" value={form.email} onChange={(e) => update("email", e.target.value)} placeholder="name@example.com" maxLength={254} /></div>
                <div className="consent-box">
                  <label className="consent-label">
                    <input type="checkbox" checked={form.consent} onChange={(e) => update("consent", e.target.checked)} />
                    <span className="custom-checkbox"><CheckCircle2 size={15} /></span>
                    <span><strong>개인정보 수집·이용에 동의합니다.</strong><small>수집 항목: 이메일 주소 · 목적: 진단 결과 발송 · 보관: 프로젝트 종료 후 30일 이내 파기 예정 · 동의를 거부할 수 있으며, 거부 시 이메일 결과 발송이 제한됩니다.</small></span>
                  </label>
                </div>
                {error && <p className="error-message" role="alert">{error}</p>}
                <button className="submit-button" type="submit">진단 시작하기 <ArrowRight size={18} /></button>
                <p className="form-footnote"><ShieldCheck size={14} /> 현재는 화면 시제품입니다. 실제 AI 분석 및 이메일 발송은 서버 연결 후 제공됩니다.</p>
              </form>
            </section>

            <section className="feature-strip">
              <div className="feature"><div className="feature-icon purple"><Bot size={21} /></div><div><strong>AI 답변 분석</strong><p>질문에 가게 이름이 등장하는지 확인</p></div></div>
              <div className="feature"><div className="feature-icon blue"><BarChart3 size={21} /></div><div><strong>경쟁 상황 파악</strong><p>같은 지역·메뉴의 다른 매장과 비교</p></div></div>
              <div className="feature"><div className="feature-icon green"><ClipboardCheck size={21} /></div><div><strong>개선 방향 제안</strong><p>실행할 수 있는 다음 행동을 안내</p></div></div>
            </section>
          </main>
          <footer><span>geo.check</span><span>GEO 진단 서비스 · 개발 중인 시제품</span><button onClick={() => setShowHelp(!showHelp)}>서비스 안내</button></footer>
        </>
      ) : (
        <main className="result-page">
          <div className="result-topline"><span className="result-pill"><WandSparkles size={14} /> DEMO PREVIEW</span><span>실제 AI 분석 결과가 아닙니다</span></div>
          <div className="result-header">
            <div className="result-symbol"><BarChart3 size={28} /></div>
            <div><div className="section-kicker">GEO DIAGNOSIS PREVIEW</div><h1>{form.storeName} <span>진단 미리보기</span></h1><p>{form.region} · 대표 메뉴: {form.menu}</p></div>
          </div>
          <div className="demo-alert"><CircleHelp size={20} /><div><strong>시제품용 예시 화면입니다.</strong><p>아래 수치와 경쟁 매장 정보는 예시이며, 실제 AI에 질의하거나 결과를 저장·발송하지 않았습니다.</p></div></div>
          <div className="result-cards">
            <div className="metric-card"><span>예시 언급률</span><strong>60<span>%</span></strong><small>샘플 데이터 · 실제 측정 아님</small></div>
            <div className="metric-card"><span>예시 질문 수</span><strong>10<span>개</span></strong><small>실제 질문 생성 전</small></div>
            <div className="metric-card"><span>분석 상태</span><strong className="pending">연결 대기</strong><small>Gemini API 연결 필요</small></div>
          </div>
          <section className="result-section">
            <div className="result-section-title"><h2>개선 제안 예시</h2><span>샘플 콘텐츠</span></div>
            <div className="recommendation"><span className="recommend-number">01</span><div><strong>매장 정보를 여러 채널에서 일관되게 관리하기</strong><p>상호, 주소, 영업시간, 대표 메뉴가 공식 웹사이트와 지도 서비스에서 동일한지 점검해 보세요.</p></div><ChevronRight size={19} /></div>
            <div className="recommendation"><span className="recommend-number">02</span><div><strong>대표 메뉴와 매장 특징을 구체적으로 설명하기</strong><p>메뉴의 차별점, 가격대, 주차 가능 여부 등 손님이 자주 궁금해하는 정보를 정리해 보세요.</p></div><ChevronRight size={19} /></div>
            <div className="recommendation"><span className="recommend-number">03</span><div><strong>손님이 실제로 검색할 질문을 준비하기</strong><p>혼밥, 가족 식사, 점심 모임 등 방문 상황에 맞는 질문으로 노출 상태를 점검할 수 있습니다.</p></div><ChevronRight size={19} /></div>
          </section>
          <div className="result-actions"><button className="secondary-button" onClick={reset}>입력 화면으로 돌아가기</button><button className="submit-button" onClick={() => window.alert("현재 시제품에서는 실제 진단·메일 발송이 연결되어 있지 않습니다.")}>실제 진단 연결 상태 확인 <ArrowRight size={17} /></button></div>
          <footer><span>geo.check</span><span>예시 결과 · 실제 AI 분석 아님</span></footer>
        </main>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
