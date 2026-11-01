// ---------- 진단 중 화면 (PRD S2, 11/1 팀장 요청: "멈춰 있는 것 같지 않게") ----------
// 서버는 진단이 끝날 때 한 번에 결과를 주고 중간 진행 상황을 보내지 않는다 (요청 1번으로 끝까지 기다리는 구조)
// → 실측 시간(10/21~22 배포 환경: 진단 22~32초, 노출률이 낮아 추가 진단이 붙으면 약 13초 더)을 기준으로 "지금쯤 이 단계"를 어림해 보여 준다
// → 진행 막대는 끝나기 전까지 92%를 넘지 않게 천천히 다가가고, 결과가 오면 화면이 결과로 바뀐다
import React, { useEffect, useState } from "react";
import { Check } from "lucide-react";

// 단계와 끝나는 시각(초). 시간 기준 어림값이라 실제와 몇 초 다를 수 있음
const STEPS = [
  { until: 4, title: "손님이 물을 만한 질문 10개 만들기", detail: "지역·메뉴·상황·조건 4가지 유형으로" },
  { until: 18, title: "AI에게 30번 물어보기", detail: "질문 10개 × 3번, 웹 검색까지 켜고" },
  { until: 26, title: "답변에서 우리 가게 찾기", detail: "나왔는지, 몇 번째인지, 어떻게 소개했는지" },
  { until: 33, title: "개선 제안 만들기", detail: "약한 곳을 바탕으로 해 볼 일 3가지" },
  { until: Infinity, title: "마무리하는 중", detail: "노출률이 낮으면 AI가 한 번 더 물어봐서 조금 더 걸려요" },
];

// 기다리는 동안 번갈아 보여 줄 한 줄 (서비스 안에서 실제로 쓰는 기준만)
const TIPS = [
  "손님은 이제 지도 앱 대신 AI에게 \"근처 맛집\"을 물어보기도 해요.",
  "AI 답변 30개 중 우리 가게가 나온 비율이 'AI 노출률'이에요.",
  "AI는 블로그·지도 리뷰·SNS를 참고해서 답해요. 어디를 많이 봤는지도 알려 드려요.",
  "함께 나온 다른 가게와 비교해서, 어떤 질문에서 약한지 찾아 드려요.",
];

export function DiagnosisProgress({ storeName }) {
  const [elapsed, setElapsed] = useState(0);                 // 시작 후 지난 시간(초)
  useEffect(() => {
    const startedAt = Date.now();
    const timer = setInterval(() => setElapsed((Date.now() - startedAt) / 1000), 250);
    return () => clearInterval(timer);                        // 결과가 와서 이 화면이 사라지면 시계도 멈춤
  }, []);

  const current = STEPS.findIndex((step) => elapsed < step.until);
  // 진행 막대: 처음엔 빠르게, 끝에 가까울수록 느리게 92%까지 (결과가 오기 전엔 100%를 찍지 않음)
  const percent = Math.min(92, 92 * (1 - Math.exp(-elapsed / 16)));
  const tip = TIPS[Math.floor(elapsed / 5) % TIPS.length];   // 5초마다 바뀜

  return (
    <div className="dp-overlay" role="status" aria-live="polite">
      <div className="dp-card">
        <p className="dp-kicker"><span className="dp-pulse" /> AI 점검 중</p>
        <h3>{storeName ? `${storeName}, ` : ""}AI에게 물어보고 있어요</h3>
        <div className="dp-bar"><div style={{ width: `${percent}%` }} /></div>
        <p className="dp-time">{Math.floor(elapsed)}초 지났어요 · 보통 20~40초 걸려요</p>

        <ol className="dp-steps">
          {STEPS.map((step, i) => {
            const state = i < current ? "done" : i === current ? "now" : "";
            return (
              <li key={step.title} className={state}>
                <span className="dp-mark">{state === "done" ? <Check size={14} /> : i + 1}</span>
                <span>
                  <strong>{step.title}</strong>
                  {state === "now" && <small>{step.detail}</small>}
                </span>
              </li>
            );
          })}
        </ol>

        <p className="dp-tip" key={tip}>{tip}</p>
        <p className="dp-note">단계 표시는 걸린 시간으로 어림한 거예요. 이 화면을 닫지 말고 기다려 주세요.</p>
      </div>
    </div>
  );
}
