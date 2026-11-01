// ---------- 결과 리포트 중간 팝업: 한 줄 질문 + 메일 보관 (11/1 팀장 결정) ----------
// 1) 피드백 전략 1 + 3 혼합: 한 가지만 묻고(탭 한 번 → 피드백 시트), 이어서 "메일로 보관할까요?"(이메일·동의 → 리포트 메일)
// 2) 같은 날 변경 ①: 리포트 안 카드는 눌러 보는 건지 몰라서 → "한눈에 보기"를 지나 내려가면 팝업으로 띄우고,
//    리포트를 이어 보려면 탭 한 번 답이 필수. 이메일은 선택으로 둠 (개인정보를 안 준다고 결과를 막지 않음, 개인정보 보호법 제16조)
// 3) 같은 날 변경 ㉠: 메일을 보낸 사장님에게만 [나머지 의견 남기기]를 권함 → 5문항 팝업(main.jsx)이 방금 답한 문항을 빼고 열림
// 묻는 칸은 맨 아래 5문항 팝업과 같은 칸을 써서 피드백 시트(Apps Script)는 고치지 않는다
import React, { useEffect, useState } from "react";
import { CheckCircle2, Mail, X } from "lucide-react";

// 무엇을 물을지: AI가 소개한 말이 있으면 그것 → 없으면 함께 나온 가게 → 둘 다 없으면 개선 제안
// 팝업은 리포트 중간에 뜨므로, 아직 안 본 내용을 물을 때는 그 내용을 힌트에 보여 줌
// 보기마다 [화면 글자, 서버에 보내는 값(팝업 보기와 같은 값)]
function questionOf(report) {
  const summary = report.summary || {};
  const quote = (summary.descriptions || [])[0];
  if (quote) {
    return { field: "accuracy", text: "AI가 소개한 우리 가게, 실제와 맞나요?", hint: `AI가 가장 많이 한 소개: “${quote.text}”`,
      options: [["맞아요", "맞음"], ["일부 맞아요", "일부 맞음"], ["달라요", "틀림"]] };
  }
  const shops = (summary.competitors || []).slice(0, 3).map((c) => c.name).filter(Boolean);
  if (shops.length) {
    return { field: "competitors", text: "AI 답변에 함께 나온 가게, 실제 경쟁 가게와 비슷한가요?", hint: `함께 나온 가게: ${shops.join(", ")}`,
      options: [["비슷해요", "비슷해요"], ["일부 비슷해요", "일부 비슷해요"], ["달라요", "달라요"]] };
  }
  const titles = (report.suggestions || []).slice(0, 3).map((s) => s.title).filter(Boolean);
  return { field: "useful", text: "개선 제안 중에 해 볼 만한 것이 있나요?",
    hint: titles.length ? `개선 제안: ${titles.join(" · ")}` : "제목만 보고 짐작으로 골라 주셔도 괜찮아요.",
    options: [["있어요", "있음"], ["없어요", "없음"]] };
}

export function ReportQuickAsk({ report, mailSentTo, onAnswered, onMailSent, onMore, onClose }) {
  const question = questionOf(report);
  const [picked, setPicked] = useState(null);       // 고른 보기 (화면 글자)
  const [step, setStep] = useState("ask");          // ask → sending → keep(메일 보관 묻기) → mailing
  const [email, setEmail] = useState("");
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState("");
  const answered = step === "keep" || step === "mailing";

  // 팝업이 떠 있는 동안 뒤의 리포트가 스크롤되지 않게 막고, 팝업이 닫히면 원래대로
  useEffect(() => {
    const before = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = before; };
  }, []);

  // 서버는 진단을 기억하지 못해서 리포트를 통째로 같이 보냄
  const post = (body) => fetch("/api/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, report }),
  }).then((response) => response.json());

  const answer = async ([label, value]) => {
    setPicked(label);
    setStep("sending");
    try {
      await post({ mode: "quick", [question.field]: value });
    } catch {
      // 저장에 실패해도 사장님 흐름은 막지 않음 (실패 이유는 서버 로그 "[feedback]"에 남음)
    }
    onAnswered(question.field, value);   // 5문항 팝업이 이 문항을 다시 묻지 않게 알려 줌
    setStep("keep");
  };

  const sendMail = async () => {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) { setError("이메일 주소를 확인해 주세요."); return; }
    if (!consent) { setError("메일로 받으려면 개인정보 수집·이용에 동의해 주세요."); return; }
    setError("");
    setStep("mailing");
    try {
      const data = await post({ mode: "mail", email: email.trim(), consent: true });
      if (!data.ok) throw new Error(data.error);
      onMailSent(email.trim());
    } catch (e) {
      setError(e.message || "리포트 메일을 보내지 못했어요. 잠시 후 다시 눌러 주세요.");
    }
    setStep("keep");
  };

  return (
    // 답하기 전에는 바깥을 눌러도, 닫기 버튼도 없음 (탭 한 번 답이 필수). 답한 뒤에는 바깥을 누르면 닫힘
    <div className="feedback-overlay" onClick={(e) => { if (answered && e.target === e.currentTarget) onClose(); }}>
      <div className="qa" role="dialog" aria-modal="true" aria-labelledby="qa-title">
        {answered && <button type="button" className="feedback-close" aria-label="닫기" onClick={onClose}><X size={18} /></button>}

        {!answered ? (
          // 1단계: 한 가지만 묻기
          <>
            <p className="qa-kicker">리포트를 이어서 보기 전에, 한 가지만 여쭤볼게요</p>
            <h3 id="qa-title">{question.text}</h3>
            <p className="qa-hint">{question.hint}</p>
            <div className="qa-options">
              {question.options.map((option) => (
                <button type="button" key={option[0]} className={picked === option[0] ? "qa-option on" : "qa-option"} onClick={() => answer(option)} disabled={step === "sending"}>
                  {option[0]}
                </button>
              ))}
            </div>
            <p className="qa-note">탭 한 번 답하시면 리포트를 이어서 볼 수 있어요. 보내 주신 답은 서비스 개선에만 써요.</p>
          </>
        ) : mailSentTo ? (
          // 메일까지 보낸 뒤: 메일을 준 사장님에게만 나머지 의견을 권함 (11/1 팀장 결정 ㉠)
          <>
            <p className="qa-kicker"><CheckCircle2 size={15} /> 메일로 보냈어요</p>
            <h3 id="qa-title">리포트를 {mailSentTo}(으)로 보냈어요</h3>
            <p className="qa-hint">몇 분 안에 도착해요. 메일이 안 보이면 스팸함도 확인해 주세요.</p>
            <div className="qa-more-box">
              <strong>1분만 더 도와주실래요?</strong>
              <span>방금 답하신 질문은 빼고, 나머지 3가지만 탭으로 여쭤볼게요. 서비스를 고치는 데 써요.</span>
            </div>
            <div className="qa-actions">
              <button type="button" className="qa-send" onClick={onMore}>나머지 의견 남기기 (1분)</button>
              <button type="button" className="qa-skip" onClick={onClose}>리포트 계속 보기</button>
            </div>
          </>
        ) : (
          // 2단계: 메일로 보관 (선택)
          <>
            <p className="qa-kicker"><CheckCircle2 size={15} /> 답해 주셔서 고마워요! ({picked})</p>
            <h3 id="qa-title">이 화면을 닫으면 결과가 사라져요.<br />메일로 보관할까요?</h3>
            <p className="qa-hint">지금 보시는 리포트와 같은 내용을 메일로 보내 드려요.</p>
            <div className="qa-form">
              <div className="input-wrap"><Mail size={16} /><input id="qa-email" type="email" value={email} maxLength={254} placeholder="이메일 (예: name@example.com)" onChange={(e) => { setEmail(e.target.value); setError(""); }} /></div>
            </div>
            <label className="qa-consent">
              <input type="checkbox" checked={consent} onChange={(e) => { setConsent(e.target.checked); setError(""); }} />
              <span><b>[필수] 개인정보 수집·이용에 동의합니다.</b> 수집 항목: 이메일 · 이용 목적: 진단 리포트 메일 발송 · 보유 기간: 2026년 11월 24일까지(이후 파기) · 동의하지 않으셔도 진단 결과는 화면에서 볼 수 있어요.</span>
            </label>
            {error && <p className="error-message">{error}</p>}
            <div className="qa-actions">
              <button type="button" className="qa-send" onClick={sendMail} disabled={step === "mailing"}>
                {step === "mailing" ? "보내는 중…" : "메일로 받기"}
              </button>
              <button type="button" className="qa-skip" onClick={onClose} disabled={step === "mailing"}>괜찮아요, 계속 볼게요</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
