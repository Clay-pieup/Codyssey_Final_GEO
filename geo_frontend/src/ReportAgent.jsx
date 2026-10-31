// ---------- 결과 리포트: AI 추가 진단 (리포트 개편, 11/1 팀장 요청: 새 스타일로) ----------
// Agent가 고른 추가 질문마다 카드 1장: 결과 뜻 한 줄(규칙) + 3번 중 몇 번 나왔나(점 3개) + AI가 고른 질문 + 고른 이유
// 추가 진단 전이면 같은 자리에 [더 자세히 진단하기] 안내 카드를 둔다 (의견 팝업이 뜨는 리포트 끝보다 먼저 보이게)
import React from "react";
import { ArrowRight } from "lucide-react";

// 질문 도구 3개의 뜻 (ai/agent.py 도구 설명을 사장님 말로) + 결과에 따른 한 줄 해석
const TOOLS = {
  "직접 지명형": {
    what: "가게 이름을 넣어 물어봐서, AI가 우리 가게를 아는지 확인해요.",
    hit: "가게 이름으로 물으면 AI가 우리 가게를 알아요",
    miss: "가게 이름으로 물어도 AI가 우리 가게를 잘 몰라요",
  },
  "경쟁 비교형": {
    what: "함께 자주 나온 가게들과 비교하게 물어봐서, 우리 가게의 위치를 확인해요.",
    hit: "다른 가게와 비교할 때도 우리 가게가 나와요",
    miss: "다른 가게와 비교할 때는 우리 가게가 빠져요",
  },
  "상황 세분형": {
    what: "혼밥·데이트처럼 상황을 더 좁혀 물어봐서, 어떤 상황에서 나오는지 확인해요.",
    hit: "상황을 좁혀 물으면 우리 가게가 나와요",
    miss: "상황을 좁혀 물어도 우리 가게가 나오지 않아요",
  },
};

function AgentCard({ item }) {
  const tool = TOOLS[item.tool_label] || {};
  const valid = item.result?.valid ?? 0;
  const hit = item.result?.mentioned ?? 0;
  const title = !valid ? "추가 질문의 답변을 받지 못했어요" : hit ? tool.hit || "추가 질문에서 우리 가게가 나왔어요" : tool.miss || "추가 질문에서도 우리 가게가 나오지 않았어요";
  return (
    <article className="ra-card">
      <div className="ra-top">
        <span className="ra-tool">{item.tool_label || "추가 질문"}</span>
        {/* 점 하나 = 답변 하나. 보라 = 우리 가게가 나온 답변 */}
        <span className="ra-dots" aria-label={`${valid}번 중 ${hit}번 나옴`}>
          {Array.from({ length: valid }, (_, i) => <i key={i} className={i < hit ? "on" : ""} />)}
        </span>
      </div>
      <h3 className={hit ? "" : "miss"}>{title}</h3>
      <p className="ra-count">추가 질문 답변 {valid}번 중 <b>{hit}번</b> 나왔어요</p>
      {tool.what && <p className="ra-what">{tool.what}</p>}
      {item.question && (
        <div className="ra-box"><span className="rq-label">AI가 고른 질문</span><p>“{item.question}”</p></div>
      )}
      <div className="ra-box"><span className="rq-label">이 질문을 고른 이유</span><p>{item.why || "별도 설명 없음"}</p></div>
    </article>
  );
}

export function ReportAgent({ report, onMore, isRunningMore, moreError }) {
  const agent = report.agent || {};
  if (!agent.ran && !report.more_available && !moreError) return null;   // 보여 줄 것이 없으면 칸 자체를 숨김

  return (
    <section className="ra">
      <div className="rp-head">
        <h2>AI 추가 진단</h2>
        <p>{agent.ran
          ? agent.trigger === "button" ? "[더 자세히 진단하기]로 AI가 스스로 질문을 골라 더 물어봤어요." : "노출률이 낮아서 AI가 스스로 질문을 골라 더 물어봤어요."
          : "AI가 질문 종류를 스스로 골라 한 번 더 물어보고, 왜 이런 결과가 나왔는지 좁혀 봐요."}</p>
      </div>

      {agent.ran ? (
        <>
          {agent.reason_to_run && <p className="ra-reason">실행 이유 · {agent.reason_to_run}</p>}
          <div className={(agent.trace || []).length > 1 ? "ra-grid two" : "ra-grid"}>
            {(agent.trace || []).map((item, i) => <AgentCard item={item} key={i} />)}
          </div>
          {!(agent.trace || []).length && <p className="rp-sub">AI가 고른 추가 질문을 실행하지 못했어요.</p>}
        </>
      ) : report.more_available ? (
        <div className="ra-cta">
          <div>
            <h3>AI에게 더 자세히 물어볼까요?</h3>
            <p>가게 이름을 넣어 묻기, 함께 나온 가게와 비교하기, 상황을 좁혀 묻기 중에서 AI가 1~2개를 골라 물어봐요. 15초쯤 걸리고, 개선 제안도 다시 만들어요.</p>
          </div>
          <button type="button" className="ra-btn" onClick={onMore} disabled={isRunningMore}>
            {isRunningMore ? "더 자세히 진단하는 중..." : <>더 자세히 진단하기 <ArrowRight size={17} /></>}
          </button>
        </div>
      ) : null}

      {moreError && <p className="ra-error" role="alert">{moreError}</p>}
    </section>
  );
}
