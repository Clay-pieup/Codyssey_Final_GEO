// ---------- 결과 리포트: 한 줄 질문 + 메일 보관 (11/1 팀장 결정: 피드백 전략 1 + 3 혼합) ----------
// 1) "한눈에 보기" 바로 아래에서 한 가지만 묻는다 → 탭 한 번이면 피드백 시트에 저장 (리포트 끝까지 안 내려도 됨)
// 3) 답하면 "이 화면을 닫으면 결과가 사라져요. 메일로 보관할까요?" → 이메일·동의(이름은 선택)로 리포트 메일
// 묻는 칸은 맨 아래 5문항 팝업과 같은 칸을 써서 피드백 시트(Apps Script)는 고치지 않는다
import React, { useState } from "react";
import { CheckCircle2, Mail, User } from "lucide-react";

// 무엇을 물을지: AI가 소개한 말이 있으면 그것 → 없으면 함께 나온 가게 → 둘 다 없으면 개선 제안
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
  return { field: "useful", text: "개선 제안 중에 해 볼 만한 것이 있나요?", hint: "아래 개선 제안을 보고 답해 주셔도 돼요.",
    options: [["있어요", "있음"], ["없어요", "없음"]] };
}

export function ReportQuickAsk({ report, mailSentTo, onAnswered, onMailSent, onMore }) {
  const question = questionOf(report);
  const [picked, setPicked] = useState(null);       // 고른 보기 (화면 글자)
  const [step, setStep] = useState("ask");          // ask → sending → keep(메일 보관 묻기) → mailing
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState("");

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
    setStep("keep");
    onAnswered();
  };

  const sendMail = async () => {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) { setError("이메일 주소를 확인해 주세요."); return; }
    if (!consent) { setError("메일로 받으려면 개인정보 수집·이용에 동의해 주세요."); return; }
    setError("");
    setStep("mailing");
    try {
      const data = await post({ mode: "mail", email: email.trim(), name: name.trim(), consent: true });
      if (!data.ok) throw new Error(data.error);
      onMailSent(email.trim());
    } catch (e) {
      setError(e.message || "리포트 메일을 보내지 못했어요. 잠시 후 다시 눌러 주세요.");
    }
    setStep("keep");
  };

  // 1단계: 한 가지만 묻기
  if (step === "ask" || step === "sending") {
    return (
      <section className="qa">
        <p className="qa-kicker">사장님께 한 가지만 여쭤볼게요</p>
        <h3>{question.text}</h3>
        <p className="qa-hint">{question.hint}</p>
        <div className="qa-options">
          {question.options.map((option) => (
            <button type="button" key={option[0]} className={picked === option[0] ? "qa-option on" : "qa-option"} onClick={() => answer(option)} disabled={step === "sending"}>
              {option[0]}
            </button>
          ))}
        </div>
        <p className="qa-note">탭 한 번이면 끝나요. 보내 주신 답은 서비스 개선에만 써요.</p>
      </section>
    );
  }

  // 2단계: 메일로 보관 (이미 보냈으면 보낸 곳 안내)
  return (
    <section className="qa">
      <p className="qa-kicker"><CheckCircle2 size={15} /> 답해 주셔서 고마워요! ({picked})</p>
      {mailSentTo ? (
        <>
          <h3>리포트를 {mailSentTo}(으)로 보냈어요</h3>
          <p className="qa-hint">몇 분 안에 도착해요. 메일이 안 보이면 스팸함도 확인해 주세요.</p>
        </>
      ) : (
        <>
          <h3>이 화면을 닫으면 결과가 사라져요.<br />메일로 보관할까요?</h3>
          <p className="qa-hint">지금 보시는 리포트와 같은 내용을 메일로 보내 드려요.</p>
          <div className="qa-form">
            <div className="input-wrap"><Mail size={16} /><input id="qa-email" type="email" value={email} maxLength={254} placeholder="이메일 (예: name@example.com)" onChange={(e) => { setEmail(e.target.value); setError(""); }} /></div>
            <div className="input-wrap"><User size={16} /><input id="qa-name" value={name} maxLength={20} placeholder="이름 (선택)" onChange={(e) => setName(e.target.value)} /></div>
          </div>
          <label className="qa-consent">
            <input type="checkbox" checked={consent} onChange={(e) => { setConsent(e.target.checked); setError(""); }} />
            <span><b>[필수] 개인정보 수집·이용에 동의합니다.</b> 수집 항목: 이메일, 이름(선택) · 이용 목적: 진단 리포트 메일 발송 · 보유 기간: 2026년 11월 24일까지(이후 파기) · 동의하지 않으셔도 진단 결과는 화면에서 볼 수 있어요.</span>
          </label>
          {error && <p className="error-message">{error}</p>}
          <button type="button" className="qa-send" onClick={sendMail} disabled={step === "mailing"}>
            {step === "mailing" ? "보내는 중…" : "메일로 받기"}
          </button>
        </>
      )}
      <button type="button" className="qa-more" onClick={onMore}>나머지 의견도 남기기 (1분)</button>
    </section>
  );
}
