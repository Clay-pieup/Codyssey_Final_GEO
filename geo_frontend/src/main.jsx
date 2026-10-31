import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowRight, BarChart3, Bot, CheckCircle2, ChevronRight, CircleHelp,
  ChevronDown, ClipboardCheck, Compass, Mail, MapPin, Search, ShieldCheck, Store,
  User, Utensils, WandSparkles, X
} from "lucide-react";
import "./styles.css";

// ---------- 결과 리포트 계산 (화면 담당과 현장 논의, 10/31) ----------

// 출처 사이트 이름: 주소는 Google 중간 주소일 수 있어 서버가 준 사이트 이름(source_sites)을 먼저 씀
function siteNames(answer) {
  const names = (answer.sources || []).map((url, i) => {
    const site = (answer.source_sites || [])[i];
    if (site) return site.replace(/^www\./, "");
    try {
      const host = new URL(url).hostname;
      return host.includes("google") ? "" : host.replace(/^www\./, "");
    } catch {
      return "";
    }
  });
  return [...new Set(names.filter(Boolean))];
}

// ---------- 사장님 의견 팝업 (피드백, 10/31 화면 담당과 현장 논의) ----------
const FEEDBACK_ASKED_KEY = "feedback-asked-v1"; // 이 브라우저에서 팝업을 이미 띄웠는지 (다시 안 띄우려고)
const EMPTY_FEEDBACK = { clarity: 0, accuracy: "", competitors: "", useful: "", comment: "", name: "", email: "", consent: false };

// 보기 중 하나를 고르는 문항 (버튼 묶음)
function Choice({ label, options, value, onPick, hint }) {
  return (
    <fieldset className="feedback-field">
      <legend>{label}</legend>
      <div className="choice-row">
        {options.map((option) => (
          <button type="button" key={option} className={value === option ? "choice on" : "choice"} aria-pressed={value === option} onClick={() => onPick(option)}>
            {option}
          </button>
        ))}
      </div>
      {hint && <small>{hint}</small>}
    </fieldset>
  );
}

// 질문 10개마다 답변 3개를 묶어 "정상 답변 중 몇 번 언급"을 센다 (서버가 Make에 보내는 질문별 결과와 같은 방식)
function questionRows(report) {
  return (report.questions || []).map((q) => {
    const answers = (report.answers || []).filter((a) => a.question_id === q.id);
    const valid = answers.filter((a) => a.status === "ok");
    return { ...q, answers, valid: valid.length, hit: valid.filter((a) => a.mentioned).length };
  });
}

function App() {
  const [form, setForm] = useState({
    storeName: "",
region: "",
menu: "",
email: "",
consent: false
  });
  const [showResult, setShowResult] = useState(false);
  const [error, setError] = useState("");
  const [diagnosisResult, setDiagnosisResult] = useState(null);
  const [isDiagnosing, setIsDiagnosing] = useState(false);
  const [moreError, setMoreError] = useState("");
  const [isRunningMore, setIsRunningMore] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [openQuestion, setOpenQuestion] = useState(null); // 결과에서 펼친 질문 (답변 원문 보기)
  const [diagnosedAt, setDiagnosedAt] = useState(null);   // 결과를 받은 시각 (리포트 "점검 시각")

  const update = (key, value) => {
    setForm((old) => ({ ...old, [key]: value }));
    setError("");
  };

  // 가게 검색: 서버(/api/places)가 네이버 지역 검색을 대신 호출 → 고르면 가게 이름·지역 자동 입력
  const [places, setPlaces] = useState([]);           // 검색 결과 목록 (최대 5개)
  const [placeMessage, setPlaceMessage] = useState(""); // 결과 없음·실패·지역 직접 입력 안내
  const [isSearching, setIsSearching] = useState(false);
  const [pickedPlace, setPickedPlace] = useState(null); // 고른 가게 (도로명 주소 확인용)

  const searchPlaces = async () => {
    const query = form.storeName.trim();
    if (query.length < 2) {
      setPlaceMessage("가게 이름을 2자 이상 입력한 뒤 검색해 주세요.");
      return;
    }
    setIsSearching(true);
    setPlaces([]);
    setPlaceMessage("");
    try {
      const response = await fetch("/api/places", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await response.json();
      setPlaces(data.places || []);
      setPlaceMessage(data.error || "");  // 검색이 실패해도 직접 입력으로 진단은 계속 가능
    } catch (e) {
      setPlaceMessage("가게 검색에 실패했어요. 직접 입력해 주세요.");
    } finally {
      setIsSearching(false);
    }
  };

  const pickPlace = (place) => {
    // 지역을 못 찾은 가게(예: 충무로2가)는 지역 칸을 그대로 두고 직접 입력 안내
    setForm((old) => ({ ...old, storeName: place.name, region: place.region || old.region }));
    setPickedPlace(place);
    setPlaces([]);
    setPlaceMessage(place.region ? "" : place.region_note);
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
      setDiagnosedAt(new Date());
      setOpenQuestion(null);
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

  // 결과 리포트에 쓰는 값 (결과 화면은 진단이 성공했을 때만 보임)
  const report = diagnosisResult || {};
  const summary = report.summary || {};
  const mention = summary.mention || {};
  const answers = report.answers || [];
  const settings = report.settings || {};
  const delivery = report.delivery || {};
  const rows = questionRows(report);

  // 사장님 의견 팝업: 리포트 맨 아래(결과 메일과 안내)까지 보면 한 번만 열림
  const [feedback, setFeedback] = useState(EMPTY_FEEDBACK);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackState, setFeedbackState] = useState("idle"); // idle → sending → done
  const [feedbackError, setFeedbackError] = useState("");
  const [feedbackResult, setFeedbackResult] = useState(null); // 서버 응답 (메일 발송 성공 여부)
  const reportEndRef = useRef(null);

  useEffect(() => {
    if (!showResult || !reportEndRef.current) return undefined;
    let asked = false;
    try { asked = localStorage.getItem(FEEDBACK_ASKED_KEY) === "1"; } catch { asked = false; }
    if (asked) return undefined;
    // 화면에 리포트 끝이 보이는 순간을 알려 주는 브라우저 기능 (스크롤 위치를 계속 계산하지 않아도 됨)
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        openFeedback();
        try { localStorage.setItem(FEEDBACK_ASKED_KEY, "1"); } catch { /* 저장이 막혀도 이번 한 번만 열림 */ }
        observer.disconnect();
      }
    }, { threshold: 0.6 });
    observer.observe(reportEndRef.current);
    return () => observer.disconnect();
  }, [showResult]);

  const pickFeedback = (key, value) => {
    setFeedback((old) => ({ ...old, [key]: value }));
    setFeedbackError("");
  };

  // 팝업을 열 때 입력 화면에서 동의하고 넣은 이메일이 있으면 미리 채움
  const openFeedback = () => {
    setFeedback((old) => ({ ...old, email: old.email || (form.consent ? form.email.trim() : "") }));
    setFeedbackOpen(true);
  };

  const sendFeedback = async () => {
    if (!feedback.clarity || !feedback.accuracy || !feedback.competitors || !feedback.useful) {
      setFeedbackError("1~4번 문항을 모두 골라 주세요.");
      return;
    }
    if (!feedback.name.trim()) {
      setFeedbackError("이름을 입력해 주세요.");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(feedback.email.trim())) {
      setFeedbackError("이메일 주소를 확인해 주세요.");
      return;
    }
    if (!feedback.consent) {
      setFeedbackError("리포트를 메일로 받으려면 개인정보 수집·이용에 동의해 주세요.");
      return;
    }
    setFeedbackState("sending");
    setFeedbackError("");
    try {
      const response = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // 서버는 진단을 기억하지 못해서 리포트를 통째로 다시 보냄 (리포트 메일 발송에 필요)
        body: JSON.stringify({ ...feedback, email: feedback.email.trim(), name: feedback.name.trim(), report }),
      });
      const data = await response.json();
      if (!data.ok) {
        setFeedbackError(data.error || "의견을 보내지 못했어요. 잠시 후 다시 보내 주세요.");
        setFeedbackState("idle");
        return;
      }
      setFeedbackResult(data);
      setFeedbackState("done");
    } catch (e) {
      setFeedbackError("의견을 보내지 못했어요. 잠시 후 다시 보내 주세요.");
      setFeedbackState("idle");
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#" onClick={(e) => { e.preventDefault(); reset(); }}>
          <span className="brand-mark"><Compass size={21} /></span>
          <span>우리가게 <span className="brand-dot">AI</span> 점검</span>
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
                <div className="search-row">
                  <div className="input-wrap">
                    <Store size={18} />
                    <input
                      id="storeName"
                      value={form.storeName}
                      onChange={(e) => { update("storeName", e.target.value); setPickedPlace(null); }}
                      onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); searchPlaces(); } }}
                      placeholder="예: 명동교자 명동"
                      maxLength={30}
                    />
                  </div>
                  <button type="button" className="search-button" onClick={searchPlaces} disabled={isSearching}>
                    <Search size={16} /> {isSearching ? "검색 중…" : "검색"}
                  </button>
                </div>
                <p className="field-help">가게 이름과 동네를 함께 넣고 [검색]을 누르면 지역이 자동으로 채워집니다. 목록에 없으면 직접 입력해도 됩니다.</p>
                {places.length > 0 && (
                  <ul className="place-list">
                    {places.map((place, index) => (
                      <li key={index}>
                        <button type="button" className="place-item" onClick={() => pickPlace(place)}>
                          <strong>{place.name}</strong>
                          <span>{place.category}</span>
                          <small>{place.road_address || place.address}</small>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
                {placeMessage && <p className="place-message">{placeMessage}</p>}

                <label htmlFor="region">지역 <span>*</span></label>
                <div className="input-wrap"><MapPin size={18} /><input id="region" value={form.region} onChange={(e) => update("region", e.target.value)} placeholder="예: 창원시 성산구 상남동" maxLength={100} /></div>
                {pickedPlace && <p className="field-help">고른 가게 주소: {pickedPlace.road_address || pickedPlace.address}</p>}

                <label htmlFor="menu">대표 메뉴 <span>*</span></label>
                <div className="input-wrap"><Utensils size={18} /><input id="menu" value={form.menu} onChange={(e) => update("menu", e.target.value)} placeholder="예: 돈가스, 냉모밀, 카레" maxLength={150} /></div>
                <p className="field-help">메뉴는 쉼표로 구분해 여러 개 입력할 수 있습니다.</p>

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
  className="submit-button"
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
                <p className="form-footnote"><ShieldCheck size={14} /> 진단 결과는 AI가 생성한 추정치입니다. 이메일은 동의한 경우에만 결과 발송에 사용합니다.</p>
              </form>
            </section>

            <section className="feature-strip">
              <div className="feature"><div className="feature-icon purple"><Bot size={21} /></div><div><strong>AI 답변 분석</strong><p>질문에 가게 이름이 등장하는지 확인</p></div></div>
              <div className="feature"><div className="feature-icon blue"><BarChart3 size={21} /></div><div><strong>경쟁 상황 파악</strong><p>같은 지역·메뉴의 다른 매장과 비교</p></div></div>
              <div className="feature"><div className="feature-icon green"><ClipboardCheck size={21} /></div><div><strong>개선 방향 제안</strong><p>실행할 수 있는 다음 행동을 안내</p></div></div>
            </section>
          </main>
          <footer><span>우리가게 AI 점검</span><span>GEO 진단 서비스 · 개발 중인 시제품</span><button onClick={() => setShowHelp(!showHelp)}>서비스 안내</button></footer>
        </>
      ) : (
        <main className="result-page">
          <div className="result-topline">
            <span className="result-pill"><WandSparkles size={14} /> AI 점검 리포트</span>
            <span>AI가 생성한 추정치입니다</span>
          </div>
          <div className="result-header">
            <div className="result-symbol"><BarChart3 size={28} /></div>
            <h1>{report.input?.store || form.storeName} <span>AI 점검 리포트</span></h1>
          </div>

          {/* 1. 어떻게 점검했나: 입력 요약 + 어떤 AI로 물어봤는지 */}
          <section className="result-section">
            <div className="result-section-title"><h2>어떻게 점검했나요</h2></div>
            <dl className="summary-grid">
              <div><dt>지역</dt><dd>{report.input?.region}</dd></div>
              <div><dt>대표 메뉴</dt><dd>{(report.input?.menus || []).join(", ")}</dd></div>
              <div><dt>물어본 AI</dt><dd>Google Gemini ({report.model}){settings.use_search ? " · 웹 검색 사용" : ""}</dd></div>
              <div><dt>질문 방식</dt><dd>손님 말투 질문 {rows.length}개 × {settings.repeat || 3}번 = 답변 {answers.length}개</dd></div>
              {diagnosedAt && <div><dt>점검 시각</dt><dd>{diagnosedAt.toLocaleString("ko-KR", { dateStyle: "medium", timeStyle: "short" })}</dd></div>}
            </dl>
          </section>

          {/* 2. 핵심 숫자 */}
          <div className="result-cards">
            <div className="metric-card">
              <span>AI 답변 속 우리 가게 언급률</span>
              <strong>{mention.rate ?? "—"}<span>%</span></strong>
              <small>정상 답변 {mention.valid ?? 0}개 중 {mention.mentioned ?? 0}개에서 언급</small>
            </div>
            <div className="metric-card">
              <span>언급될 때 평균 순위</span>
              <strong>{summary.rank?.average ?? "—"}<span>{summary.rank?.average != null ? "위" : ""}</span></strong>
              <small>{summary.rank?.counted ? `여러 가게를 나열한 답변 ${summary.rank.counted}개 기준, 1위 ${summary.rank.first_place}번` : "여러 가게를 나열한 답변에서 순위를 셀 수 없음"}</small>
            </div>
            <div className="metric-card">
              <span>받은 AI 답변</span>
              <strong>{mention.valid ?? 0}<span>개</span></strong>
              <small>전체 {answers.length}개 중 정상 답변 (실패·빈 답변은 언급률에서 제외)</small>
            </div>
          </div>
          {summary.low_reliability && (
            <div className="demo-alert" role="note">
              <CircleHelp size={20} />
              <div><strong>신뢰도 낮음</strong><p>정상적으로 받은 AI 답변이 충분하지 않아 결과가 실제와 다를 수 있어요. 참고 자료로만 봐 주세요.</p></div>
            </div>
          )}

          {/* 3. 질문 유형별 */}
          <section className="result-section">
            <div className="result-section-title"><h2>질문 유형별 결과</h2><span>손님이 어떻게 물을 때 나오나요</span></div>
            {Object.entries(summary.by_type || {}).map(([type, v]) => (
              <div className="type-row" key={type}>
                <strong>{type}</strong>
                <div className="type-bar"><div style={{ width: `${v.rate ?? 0}%` }} /></div>
                <span>{v.valid ? `${v.valid}개 중 ${v.mentioned ?? 0}개` : "측정 불가"}</span>
              </div>
            ))}
          </section>

          {/* 4. 질문별 결과 + AI 답변 원문 */}
          <section className="result-section">
            <div className="result-section-title"><h2>AI에게 물어본 질문 {rows.length}개</h2><span>질문을 누르면 AI 답변 원문</span></div>
            <ol className="question-list">
              {rows.map((q) => (
                <li key={q.id}>
                  <button type="button" className="question-row" aria-expanded={openQuestion === q.id} onClick={() => setOpenQuestion(openQuestion === q.id ? null : q.id)}>
                    <span className="question-type">{q.type}</span>
                    <span className="question-text">{q.text}</span>
                    <span className={q.hit > 0 ? "hit-badge yes" : "hit-badge"}>{q.valid ? `${q.valid}번 중 ${q.hit}번 언급` : "답변 없음"}</span>
                    <ChevronDown size={16} className={openQuestion === q.id ? "chevron open" : "chevron"} />
                  </button>
                  {openQuestion === q.id && (
                    <div className="answer-list">
                      {q.answers.map((a) => (
                        <div className="answer-item" key={a.run}>
                          <div className="answer-head">
                            <strong>{a.run}번째 답변</strong>
                            <span className={a.status === "ok" && a.mentioned ? "yes" : ""}>
                              {a.status !== "ok" ? "답변 실패 (언급률 계산에서 제외)" : a.mentioned ? `우리 가게 언급${a.rank ? ` · ${a.rank}위` : ""}` : "언급 없음"}
                            </span>
                          </div>
                          {a.text && <p className="answer-text">{a.text.replace(/\*\*/g, "")}</p>}
                          {siteNames(a).length > 0 && <p className="answer-sources">출처: {siteNames(a).slice(0, 5).join(", ")}</p>}
                        </div>
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ol>
          </section>

          {/* 5. AI가 우리 가게를 소개한 말 (사장님 설문 "소개한 말이 실제와 맞았나요?"와 연결) */}
          <section className="result-section">
            <div className="result-section-title"><h2>AI가 우리 가게를 소개한 말</h2></div>
            {(summary.descriptions || []).length > 0 ? (
              <ul className="quote-list">
                {summary.descriptions.map((d, i) => (
                  <li key={i}>“{d.text}” <small>{d.count}번</small></li>
                ))}
              </ul>
            ) : (
              <p className="muted">AI 답변에서 우리 가게를 소개한 말이 없어요{mention.mentioned ? "" : " (우리 가게가 언급된 답변이 없음)"}.</p>
            )}
          </section>

          {/* 6. 함께 나온 가게 */}
          <section className="result-section">
            <div className="result-section-title"><h2>AI 답변에 함께 나온 가게</h2></div>
            {(summary.competitors || []).length > 0 ? (
              summary.competitors.slice(0, 3).map((c, index) => (
                <div className="recommendation" key={index}>
                  <span className="recommend-number">{String(index + 1).padStart(2, "0")}</span>
                  <div>
                    <strong>{c.name}</strong>
                    <p>{c.description || "소개 문장 없음"}</p>
                    <small>함께 나온 답변 {c.answers ?? 0}개</small>
                  </div>
                </div>
              ))
            ) : (
              <p className="muted">함께 나온 다른 가게가 없어요.</p>
            )}
          </section>

          {/* 7. AI 추가 진단 (Agent) */}
          {report.agent?.ran && (
            <section className="result-section">
              <div className="result-section-title"><h2>AI 추가 진단</h2><span>{report.agent.trigger === "button" ? "더 자세히 진단하기" : "언급률이 낮아 자동 실행"}</span></div>
              {report.agent.reason_to_run && <p className="muted">{report.agent.reason_to_run}</p>}
              {(report.agent.trace || []).map((item, index) => (
                <div className="recommendation" key={index}>
                  <span className="recommend-number">{String(index + 1).padStart(2, "0")}</span>
                  <div>
                    <strong>{item.tool_label || "추가 진단"}</strong>
                    {item.question && <p>추가 질문: "{item.question}"</p>}
                    <p>AI가 이 질문을 고른 이유: {item.why || "별도 설명 없음"}</p>
                    <small>결과: 정상 답변 {item.result?.valid ?? 0}개 중 {item.result?.mentioned ?? 0}개에서 언급</small>
                  </div>
                </div>
              ))}
            </section>
          )}

          {/* 8. 개선 제안 */}
          <section className="result-section">
            <div className="result-section-title"><h2>개선 제안</h2><span>근거는 위 진단 결과</span></div>
            {(report.suggestions || []).length > 0 ? (
              report.suggestions.slice(0, 3).map((sg, index) => (
                <div className="recommendation" key={index}>
                  <span className="recommend-number">{String(index + 1).padStart(2, "0")}</span>
                  <div>
                    <strong>{sg.title}</strong>
                    <p>{sg.detail}</p>
                    {sg.evidence && <small>근거: {sg.evidence}</small>}
                  </div>
                </div>
              ))
            ) : (
              <p className="muted">개선 제안을 만들지 못했어요. 다시 진단해 주세요.</p>
            )}
          </section>

          {/* 9. 결과 메일 + 안내 */}
          <section className="result-section" ref={reportEndRef}>
            <div className="result-section-title"><h2>결과 메일과 안내</h2></div>
            <p className="muted">
              <Mail size={14} />{" "}
              {!delivery.requested
                ? "이메일을 입력하지 않아 결과 메일은 보내지 않았어요."
                : delivery.sent
                  ? "입력하신 이메일로 결과를 보냈어요. 몇 분 안에 도착해요."
                  : "결과 메일을 보내지 못했어요. 이 화면을 저장해 두세요."}
            </p>
            {report.notice && <p className="muted">{report.notice}</p>}
          </section>

          {moreError && (
            <div className="demo-alert" role="alert">
              <CircleHelp size={20} />
              <p>{moreError}</p>
            </div>
          )}

          <div className="result-actions">
            <button className="secondary-button" onClick={reset}>입력 화면으로 돌아가기</button>
            <button className="secondary-button" onClick={openFeedback} disabled={feedbackState === "done"}>
              {feedbackState === "done" ? "의견 고맙습니다" : "의견 남기고 리포트 받기"}
            </button>
            {report.more_available && (
              <button className="submit-button" onClick={runMoreDiagnosis} disabled={isRunningMore}>
                {isRunningMore ? "더 자세히 진단하는 중..." : "더 자세히 진단하기"}
                <ArrowRight size={17} />
              </button>
            )}
          </div>
          {feedbackOpen && (
            <div className="feedback-overlay" onClick={(e) => { if (e.target === e.currentTarget) setFeedbackOpen(false); }}>
              <div className="feedback-modal" role="dialog" aria-modal="true" aria-labelledby="feedback-title">
                <button type="button" className="feedback-close" aria-label="닫기" onClick={() => setFeedbackOpen(false)}><X size={18} /></button>
                {feedbackState === "done" ? (
                  <div className="feedback-done">
                    <CheckCircle2 size={30} />
                    <h3>고맙습니다!</h3>
                    <p>
                      {feedbackResult?.mail_sent
                        ? `리포트를 ${feedback.email.trim()}(으)로 보냈어요. 몇 분 안에 도착해요.`
                        : "의견은 잘 받았어요. 다만 리포트 메일을 보내지 못했어요. 이 화면을 저장해 두세요."}
                    </p>
                    <button className="submit-button" onClick={() => setFeedbackOpen(false)}>닫기</button>
                  </div>
                ) : (
                  <>
                    <h3 id="feedback-title">사장님 의견을 들려주시면 리포트를 메일로 발송해드립니다.</h3>
                    <p className="feedback-note">리포트를 보신 그대로 답해 주세요. 5문항(1~4번 필수), 1분이면 끝나요.</p>
                    <Choice label="1. 진단 결과(언급률·질문별 결과)를 이해하기 쉬웠나요?" options={[1, 2, 3, 4, 5]} value={feedback.clarity} onPick={(v) => pickFeedback("clarity", v)} hint="1 어려웠어요 · 5 쉬웠어요" />
                    <Choice label="2. 'AI가 우리 가게를 소개한 말'이 실제 가게와 맞았나요?" options={["맞음", "일부 맞음", "틀림", "소개 없음"]} value={feedback.accuracy} onPick={(v) => pickFeedback("accuracy", v)} />
                    <Choice label="3. 'AI 답변에 함께 나온 가게'가 실제 경쟁 가게와 비슷했나요?" options={["비슷해요", "일부 비슷해요", "달라요", "잘 모르겠어요"]} value={feedback.competitors} onPick={(v) => pickFeedback("competitors", v)} />
                    <Choice label="4. '개선 제안' 중 실제로 해 볼 만한 것이 있었나요?" options={["있음", "없음"]} value={feedback.useful} onPick={(v) => pickFeedback("useful", v)} />
                    <fieldset className="feedback-field">
                      <legend>5. 리포트에서 불편했거나 더 보고 싶은 내용 (선택)</legend>
                      <textarea value={feedback.comment} maxLength={300} placeholder="자유롭게 적어 주세요" onChange={(e) => pickFeedback("comment", e.target.value)} />
                    </fieldset>

                    <div className="feedback-contact">
                      <strong>리포트 받을 정보</strong>
                      <label htmlFor="fb-name">이름 <span>*</span></label>
                      <div className="input-wrap"><User size={16} /><input id="fb-name" value={feedback.name} maxLength={20} placeholder="예: 홍길동" onChange={(e) => pickFeedback("name", e.target.value)} /></div>
                      <label htmlFor="fb-email">이메일 <span>*</span></label>
                      <div className="input-wrap"><Mail size={16} /><input id="fb-email" type="email" value={feedback.email} maxLength={254} placeholder="name@example.com" onChange={(e) => pickFeedback("email", e.target.value)} /></div>
                      <div className="consent-box">
                        <label className="consent-label">
                          <input type="checkbox" checked={feedback.consent} onChange={(e) => pickFeedback("consent", e.target.checked)} />
                          <span className="custom-checkbox"><CheckCircle2 size={15} /></span>
                          <span>
                            <strong>[필수] 아래 내용을 확인했으며, 개인정보 수집·이용에 동의합니다.</strong>
                            <small>수집 항목: 이름, 이메일 · 이용 목적: 진단 리포트 메일 발송과 보내 주신 의견 확인 · 보유 기간: 2026년 11월 24일까지(이후 파기) · 동의하지 않으셔도 진단 결과는 화면에서 볼 수 있지만, 리포트 메일은 받을 수 없어요.</small>
                          </span>
                        </label>
                      </div>
                    </div>

                    {feedbackError && <p className="error-message">{feedbackError}</p>}
                    <div className="feedback-actions">
                      <button className="secondary-button" onClick={() => setFeedbackOpen(false)}>나중에 할게요</button>
                      <button className="submit-button" onClick={sendFeedback} disabled={feedbackState === "sending"}>
                        {feedbackState === "sending" ? "보내는 중…" : "의견 보내고 리포트 받기"}
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          <footer>
            <span>우리가게 AI 점검</span>
            <span>AI가 생성한 추정치 · 실제 AI 앱 답변과 다를 수 있음</span>
          </footer>
        </main>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
