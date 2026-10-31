// ---------- 결과 리포트: 개선 제안 (리포트 개편 단위 3, 10/31 팀장 결정: 시안 ㉠ + ㉡) ----------
// ㉡ 가장 먼저 할 일 하나를 크게 + 나머지는 체크리스트
// ㉠ 진단에서 약했던 곳과 제안을 같은 번호·색으로 이어 "왜 이걸 해야 하지?"를 보여 줌
// AI가 주는 칸(title·detail·evidence)은 그대로 쓰고, 약한 곳 찾기와 연결은 화면 코드가 규칙으로 한다
import React, { useState } from "react";
import { Ring, josa } from "./ReportDashboard.jsx";

const TAG_COLORS = ["#6655db", "#3f8fd0", "#e08a3c"];   // 제안 1·2·3번 색 (흰 글자가 잘 보이는 진한 색)

// 약한 곳 목록: 질문 유형별 결과 + 추가 질문(Agent) 결과 + 가장 많이 나온 가게와의 비교. 비율이 낮은 순
function weakSpots(report) {
  const summary = report.summary || {};
  const spots = [];
  Object.entries(summary.by_type || {}).forEach(([type, v]) => {
    if (v.valid) spots.push({ label: `${type} 질문`, hit: v.mentioned || 0, of: v.valid, words: [type] });
  });
  (report.agent?.trace || []).forEach((t) => {
    const r = t.result || {};
    if (r.valid && t.tool_label) spots.push({ label: `추가 질문 · ${t.tool_label}`, hit: r.mentioned || 0, of: r.valid, words: [t.tool_label] });
  });
  const top = (summary.competitors || [])[0];
  const ours = summary.mention?.mentioned || 0;
  if (top && (top.answers || 0) > ours) {
    spots.push({ label: `${josa(top.name, "과", "와")} 비교`, hit: ours, of: top.answers, words: [top.name], text: `${ours} : ${top.answers}` });
  }
  return spots.sort((a, b) => a.hit / a.of - b.hit / b.of);
}

// 제안 → 약한 곳 연결: 근거 문장에 약한 곳 이름(예: "메뉴형", "경쟁 비교형", 가게 이름)이 있으면 그 약한 곳과 잇는다
// 근거에 없으면 제목·설명에서 찾고, 여러 개면 더 약한 곳(목록 앞쪽)을 고른다
function linkOf(suggestion, spots) {
  for (const field of [suggestion.evidence, `${suggestion.title} ${suggestion.detail}`]) {
    const index = spots.findIndex((spot) => spot.words.some((word) => word && String(field || "").includes(word)));
    if (index >= 0) return index;
  }
  return -1;
}

// 근거 문장 속 "9개 중 2개" → { hit: 2, of: 9 } (원형 그림용). 없으면 연결된 약한 곳의 숫자를 씀
function numbersOf(evidence, spot) {
  const m = String(evidence || "").match(/(\d+)\s*개[^0-9]{0,6}?중\s*(\d+)\s*개/);   // "9개 중 2개", "9개 답변 중 2개"
  if (m && Number(m[1]) > 0) return { hit: Number(m[2]), of: Number(m[1]) };
  return spot ? { hit: spot.hit, of: spot.of } : null;
}

export function ReportSuggestions({ report }) {
  const suggestions = (report.suggestions || []).slice(0, 3);
  const spots = weakSpots(report);
  const items = suggestions.map((s, i) => {
    const link = linkOf(s, spots);
    return { ...s, no: i + 1, color: TAG_COLORS[i], link, spot: spots[link], nums: numbersOf(s.evidence, spots[link]) };
  });
  const [picked, setPicked] = useState(() => new Set());          // "해 볼게요"를 고른 제안 번호 (화면에서만, 저장 안 함)
  const toggle = (no) => setPicked((old) => {
    const next = new Set(old);
    if (next.has(no)) next.delete(no); else next.add(no);
    return next;
  });

  if (!items.length) {
    return (
      <section className="rp-actions">
        <div className="rp-head"><h2>개선 제안</h2></div>
        <p className="rp-sub">개선 제안을 만들지 못했어요. 다시 진단해 주세요.</p>
      </section>
    );
  }

  // 가장 먼저 할 일: 가장 약한 곳과 이어진 제안. 연결된 제안이 없으면 AI가 첫 번째로 낸 제안
  const linked = items.filter((it) => it.link >= 0).sort((a, b) => a.link - b.link || a.no - b.no);
  const first = linked[0] || items[0];
  const rest = items.filter((it) => it.no !== first.no);

  // 어떤 제안과도 이어지지 않은 가장 약한 곳 (0번 나온 곳만 알려 줌)
  const linkedSpots = new Set(items.map((it) => it.link));
  const missed = spots.find((spot, i) => spot.hit === 0 && !linkedSpots.has(i));

  return (
    <section className="rp-actions">
      <div className="rp-head"><h2>개선 제안</h2><p>진단에서 약했던 곳을 바탕으로 해 볼 일을 골랐어요.</p></div>

      {/* ㉡ 가장 먼저 할 일 */}
      <div className="rp-spot">
        <div>
          <p className="rp-spot-kicker"><span className="rp-tag" style={{ background: "#ffffff33" }}>{first.no}</span>가장 먼저 해 볼 일</p>
          <h3>{first.title}</h3>
          <p className="rp-spot-detail">{first.detail}</p>
          {first.evidence && <p className="rp-spot-why">왜? {first.evidence}</p>}
          <p className="rp-spot-reason">{first.link >= 0 ? `${josa(first.spot.label, "이", "가")} 약해서 먼저 골랐어요 (${first.spot.text || `${first.spot.hit}/${first.spot.of}`}).` : "AI가 첫 번째로 낸 제안이에요."}</p>
          <button type="button" className="rp-spot-btn" aria-pressed={picked.has(first.no)} onClick={() => toggle(first.no)}>
            {picked.has(first.no) ? "해 볼 일에 담았어요" : "해 볼게요"}
          </button>
        </div>
        {first.nums && (
          <div className="rp-spot-ring">
            <Ring size={112} stroke={14} track="#ffffff40"
              parts={[{ label: "나옴", value: first.nums.hit, color: "#ffffff" }, { label: "안 나옴", value: first.nums.of - first.nums.hit, color: "transparent" }]} />
            <span>{first.nums.hit}/{first.nums.of}<small>지금</small></span>
          </div>
        )}
      </div>

      <div className="rp-act-grid">
        {/* ㉠ 약한 곳 → 할 일 연결 */}
        <div className="rp-weak">
          <p className="rp-kicker">AI 답변에서 약한 곳</p>
          {spots.map((spot, i) => ({ spot, i })).filter(({ i }) => i < 4 || linkedSpots.has(i)).map(({ spot, i }) => {   // 가장 약한 4곳 + 제안과 이어진 곳
            const owner = items.find((it) => it.link === i);
            return (
              <div className="rp-weak-row" key={spot.label}>
                <span className={owner ? "rp-tag" : "rp-tag none"} style={owner ? { background: owner.color } : undefined} title={owner ? `${owner.no}번 제안과 연결` : "연결된 제안 없음"}>{owner ? owner.no : "–"}</span>
                <span className="rp-weak-label">{spot.label}</span>
                <b>{spot.text || `${spot.hit}/${spot.of}`}</b>
                <span className="rp-weak-bar"><i style={{ width: `${Math.max(3, (spot.hit / spot.of) * 100)}%` }} /></span>
              </div>
            );
          })}
          {missed && <p className="rp-missed">{missed.label}({missed.hit}/{missed.of})에 대한 제안은 아직 없어요.</p>}
        </div>

        {/* ㉡ 나머지는 체크리스트 */}
        <div className="rp-todos">
          <div className="rp-progress"><span>{items.length}개 중 {picked.size}개 해 볼게요</span><span className="rp-progress-track"><i style={{ width: `${(picked.size / items.length) * 100}%` }} /></span></div>
          {rest.map((it) => (
            <label className="rp-todo" key={it.no}>
              <input type="checkbox" checked={picked.has(it.no)} onChange={() => toggle(it.no)} />
              <span className="rp-todo-body">
                <span className="rp-todo-top"><span className="rp-tag" style={{ background: it.color }}>{it.no}</span>{it.spot ? `약한 곳: ${it.spot.label}` : "근거를 바탕으로 한 제안"}</span>
                <strong>{it.title}</strong>
                <span className="rp-todo-detail">{it.detail}</span>
                {it.evidence && <span className="rp-todo-ev">근거: {it.evidence}</span>}
              </span>
            </label>
          ))}
        </div>
      </div>
    </section>
  );
}
