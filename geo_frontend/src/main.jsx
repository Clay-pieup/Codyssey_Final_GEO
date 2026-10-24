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
    storeName: "",
region: "",
menu: "",
station: "",
email: "",
consent: false
  });
  const [showResult, setShowResult] = useState(false);
  const [diagnosisResult, setDiagnosisResult] = useState(null);
  const [isDiagnosing, setIsDiagnosing] = useState(false);
  const [moreError, setMoreError] = useState("");
  const [isRunningMore, setIsRunningMore] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  const update = (key, value) => {
    setForm((old) => ({ ...old, [key]: value }));
    setError("");
  };

  const startDiagnosis = async (event) => {
    event.preventDefault();
    if (!form.storeName.trim() || !form.region.trim() || !form.menu.trim() ) {
      setError("상호, 지역, 대표 메뉴를 모두 입력해 주세요.");
      return;
    }
     const menus = form.menu
      .split(",")
      .map((menu) => menu.trim())
      .filter(Boolean);

     if (menus.length < 1 || menus.length > 3) {
       setError("대표 메뉴는 쉼표(,)로 구분하여 1~3개 입력해 주세요.");
       return;
    }

    if (form.email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
      setError("이메일 주소를 확인해 주세요.");
      return;
    }
    
    if (form.email.trim() && !form.consent) {
       setError("이메일로 결과를 받으려면 개인정보 수집·이용에 동의해 주세요.");
       return;
    }
    
            setError("");
    setDiagnosisResult(null);
    setIsDiagnosing(true);

    try {
      const response = await fetch("/api/diagnose", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          store: form.storeName.trim(),
          region: form.region.trim(),
          menus,
          station: form.station.trim(),
          email: form.email.trim(),
          consent: form.consent,
        }),
      });

      const report = await response.json();

      if (!response.ok || !report.ok) {
        const problems = Array.isArray(report.problems)
          ? report.problems.join("\n")
          : "";

        setError(
          [report.error || "진단 중 오류가 발생했습니다.", problems]
            .filter(Boolean)
            .join("\n")
        );
        return;
      }

      setDiagnosisResult(report);
      setShowResult(true);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (error) {
      setError("서버 연결에 실패했습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      setIsDiagnosing(false);
    }
  };

  const reset = () => {
  setShowResult(false);
  setDiagnosisResult(null);
  setError("");
  setMoreError("");
  window.scrollTo({ top: 0, behavior: "smooth" });
};

  const runMoreDiagnosis = async () => {
  if (!diagnosisResult?.ok || !diagnosisResult.more_available || isRunningMore) {
    return;
  }

  setMoreError("");
  setIsRunningMore(true);

  try {
    const response = await fetch("/api/more", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        report: diagnosisResult,
        email: form.email.trim(),
        consent: form.consent,
      }),
    });

    const report = await response.json();

    if (!response.ok || !report.ok || report.more_error) {
      setMoreError(
        report.more_error ||
        report.error ||
        "추가 진단 중 오류가 발생했습니다."
      );
      return;
    }

    setDiagnosisResult(report);
  } catch (error) {
    setMoreError("서버 연결에 실패했습니다. 잠시 후 다시 시도해 주세요.");
  } finally {
    setIsRunningMore(false);
  }
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
                <p className="section-desc">매장 정보를 입력해 주세요.<br />이메일을 입력하고 개인정보 수집·이용에 동의하시면, 서비스 연동 후 진단 결과를 이메일로 받아보실 수 있습니다.</p>
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
                <div className="input-wrap"><Store size={18} /><input id="storeName" value={form.storeName} onChange={(e) => update("storeName", e.target.value)} placeholder="예: 소담 돈가스" maxLength={30} /></div>

                <label htmlFor="region">지역 <span>*</span></label>
                <div className="input-wrap"><MapPin size={18} /><input id="region" value={form.region} onChange={(e) => update("region", e.target.value)} placeholder="예: 창원시 성산구 상남동" maxLength={100} /></div>

                <label htmlFor="menu">대표 메뉴 <span>*</span></label>
                <div className="input-wrap"><Utensils size={18} /><input id="menu" value={form.menu} onChange={(e) => update("menu", e.target.value)} placeholder="예: 돈가스, 냉모밀, 카레" maxLength={150} /></div>
                <p className="field-help">메뉴는 쉼표로 구분해 여러 개 입력할 수 있습니다.</p>
                <label htmlFor="station">가까운 역 (선택)</label>
                <div className="input-wrap">
                  <MapPin size={18} />
                  <input
                    id="station"
                    value={form.station}
                    onChange={(e) => update("station", e.target.value)}
                    placeholder="예: 서울역 (없으면 비워두세요)"
                    maxLength={20}
                  />
               </div>
               <p className="field-help">
                  가까운 역이 있는 경우에만 입력해 주세요.
               </p>

                <div className="form-divider" />
                <label htmlFor="email">결과 받을 이메일 (선택)</label>
                <div className="input-wrap"><Mail size={18} /><input id="email" type="email" value={form.email} onChange={(e) => update("email", e.target.value)} placeholder="name@example.com" maxLength={254} disabled={!form.consent} />
                </div>
                <div className="consent-box">
                  <label className="consent-label">
                    <input
  type="checkbox"
  checked={form.consent}
  onChange={(e) => {
    const checked = e.target.checked;
    setForm((old) => ({
      ...old,
      consent: checked,
      email: checked ? old.email : ""
    }));
    setError("");
  }}
/>
                    <span className="custom-checkbox"><CheckCircle2 size={15} /></span>
                    <span><strong>개인정보 수집·이용에 동의합니다.</strong><small>수집 항목: 이메일 주소 · 목적: 진단 결과 발송 · 보관: 2026-11-24 파기 · 동의를 거부할 수 있으며, 거부 시 이메일 결과 발송이 제한됩니다.</small></span>
                  </label>
                </div>
                {error && <p className="error-message" role="alert">{error}</p>}
                <button
  className="primary-button"
  type="submit"
  disabled={isDiagnosing}
>
  {isDiagnosing ? (
    "진단 중… 최대 1~2분"
  ) : (
    <>
      진단 시작하기 <ArrowRight size={18} />
    </>
  )}
</button>
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
          <div className="result-topline">
  <span className="result-pill">
    <WandSparkles size={14} />
    {diagnosisResult?.ok ? "AI DIAGNOSIS RESULT" : "DEMO PREVIEW"}
  </span>
  <span>
    {diagnosisResult?.ok
      ? "AI가 생성한 분석 결과입니다."
      : "실제 AI 분석 결과가 아닙니다"}
  </span>
</div>
          <div className="result-header">
            <div className="result-symbol"><BarChart3 size={28} /></div>
            <h1>
  {form.storeName}{" "}
  <span>{diagnosisResult?.ok ? "AI 진단 결과" : "진단 미리보기"}</span>
</h1>
          </div>
          {!diagnosisResult?.ok && (
  <div className="demo-alert">
    <CircleHelp size={20} />
    <div>
      <strong>시제품용 예시 화면입니다.</strong>
      <p>
        아래 수치와 경쟁 매장 정보는 예시이며,
        실제 AI에 질의하거나 결과를 저장·발송하지 않았습니다.
      </p>
    </div>
    </div>
)}
<div className="result-cards">
          <div className="metric-card">
  <span>{diagnosisResult?.ok ? "AI 매장 언급률" : "예시 언급률"}</span>
  <strong>
    {diagnosisResult?.ok
      ? `${diagnosisResult.summary?.mention?.rate ?? "—"}`
      : "60"}
    <span>%</span>
  </strong>
  <small>
    {diagnosisResult?.ok ? "AI 진단 결과" : "샘플 데이터 · 실제 측정 아님"}
  </small>
</div>  
            <div className="metric-card">
  <span>{diagnosisResult?.ok ? "AI 진단 질문 수" : "예시 질문 수"}</span>
  <strong>
    {diagnosisResult?.ok
      ? diagnosisResult.questions?.length ?? 0
      : 10}
    <span>개</span>
  </strong>
  <small>
    {diagnosisResult?.ok ? "실제 생성된 질문 기준" : "실제 질문 생성 전"}
  </small>
</div>
            <div className="metric-card">
  <span>분석 상태</span>
  <strong className={diagnosisResult?.ok ? "" : "pending"}>
    {diagnosisResult?.ok ? "진단 완료" : "연결 대기"}
  </strong>
  <small>
    {diagnosisResult?.ok
      ? "AI 진단 결과 수신 완료"
      : "Gemini API 연결 필요"}
  </small>
</div>
          </div>
          {diagnosisResult?.ok && diagnosisResult.summary?.by_type && (
  <section className="result-section">
    <div className="result-section-title">
      <h2>질문 유형별 AI 언급 결과</h2>
    </div>

    {Object.entries(diagnosisResult.summary.by_type).map(
      ([type, result]) => (
        <div className="recommendation" key={type}>
          <div>
            <strong>{type}</strong>
            <p>
              정상 답변 {result.valid ?? 0}개 중
              {" "}{result.mentioned ?? 0}개 언급
              {" "}(
              {result.rate == null ? "측정 불가" : `${result.rate}%`}
              )
            </p>
          </div>
        </div>
      )
    )}
   </section>
)} 

  {diagnosisResult?.ok && (
  <section className="result-section">
    <div className="result-section-title">
      <h2>AI 답변에 함께 등장한 가게</h2>
    </div>

    {(diagnosisResult.summary?.competitors ?? []).length > 0 ? (
      diagnosisResult.summary.competitors.slice(0, 3).map((competitor, index) => (
        <div className="recommendation" key={index}>
          <span className="recommend-number">
            {String(index + 1).padStart(2, "0")}
          </span>
          <div>
            <strong>{competitor.name}</strong>
            <p>{competitor.description || "소개 문장 없음"}</p>
            <small>함께 등장한 답변: {competitor.answers ?? 0}개</small>
          </div>
        </div>
      ))
    ) : (
      <p>함께 언급된 다른 가게가 없습니다.</p>
    )}
  </section>
)}
{diagnosisResult?.ok && diagnosisResult.agent?.ran && (
  <section className="result-section">
    <div className="result-section-title">
      <h2>AI 추가 진단 결과</h2>
    </div>

    {diagnosisResult.agent.reason_to_run && (
      <p>{diagnosisResult.agent.reason_to_run}</p>
    )}

    {(diagnosisResult.agent.trace ?? []).map((item, index) => (
      <div className="recommendation" key={index}>
        <span className="recommend-number">
          {String(index + 1).padStart(2, "0")}
        </span>
        <div>
          <strong>{item.tool_label || "추가 진단"}</strong>
          <p>선택 이유: {item.why || "별도 설명 없음"}</p>
          <small>
            언급 결과: {item.result?.mentioned ?? 0}개 /
            정상 답변 {item.result?.valid ?? 0}개
          </small>
        </div>
      </div>
    ))}
  </section>
)}

<section className="result-section">
            <div className="result-section-title">
  <h2>
    {diagnosisResult?.ok ? "AI 맞춤 개선 제안" : "개선 제안 예시"}
  </h2>
  <span>{diagnosisResult?.ok ? "AI 분석 결과" : "샘플 콘텐츠"}</span>
</div>
            {diagnosisResult?.ok ? (
  (diagnosisResult.suggestions ?? []).slice(0, 3).map((suggestion, index) => (
    <div className="recommendation" key={index}>
      <span className="recommend-number">
        {String(index + 1).padStart(2, "0")}
      </span>
      <div>
        <strong>{suggestion.title}</strong>
        <p>{suggestion.detail}</p>
        {suggestion.evidence && (
          <small>분석 근거: {suggestion.evidence}</small>
        )}
      </div>
      <ChevronRight size={19} />
    </div>
  ))
) : (
  <p>AI 진단을 실행하면 맞춤 개선 제안이 표시됩니다.</p>
)}
          </section>

        {diagnosisResult?.ok && diagnosisResult.notice && (
  <section className="result-section">
    <div className="result-section-title">
      <h2>진단 결과 안내</h2>
    </div>
    <p>{diagnosisResult.notice}</p>
  </section>
)}  

{diagnosisResult?.ok && diagnosisResult.summary?.low_reliability && (
  <section className="result-section">
    <div className="result-section-title">
      <h2>분석 신뢰도 안내</h2>
    </div>
    <p>
      정상적으로 수집된 AI 답변이 충분하지 않아
      진단 결과의 신뢰도가 낮을 수 있습니다.
      결과를 참고 자료로 활용해 주세요.
    </p>
  </section>
)}
          {moreError && (
  <div className="demo-alert" role="alert">
    <CircleHelp size={20} />
    <p>{moreError}</p>
  </div>
)}

<div className="result-actions"></div>

          <div className="result-actions"><button className="secondary-button" onClick={reset}>입력 화면으로 돌아가기</button>{diagnosisResult?.ok && diagnosisResult.more_available && (
  <button
    className="submit-button"
    onClick={runMoreDiagnosis}
    disabled={isRunningMore}
  >
    {isRunningMore ? "AI 추가 진단 중..." : "AI 추가 진단하기"}
    <ArrowRight size={17} />
  </button>
)}
</div>
          <footer>
  <span>geo.check</span>
  <span>
    {diagnosisResult?.ok
      ? "실제 AI 진단 결과"
      : "예시 결과 · 실제 AI 분석 아님"}
  </span>
</footer>
        </main>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
