// ---------- 결과 리포트 맨 위: 요약 띠 + "한눈에 보기" 대시보드 (리포트 개편 단위 2, 10/31 팀장 결정) ----------
// 시안: 토스 비즈니스 느낌(큰 숫자, 회색 카드, 카드마다 한 줄 결론), 앱 색(보라) 기준
// 그래프는 새 라이브러리 없이 직접 그린다: 막대 = 칸 너비(%), 도넛 = SVG 원의 테두리를 비율만큼 칠하기
// 카드의 한 줄 결론은 AI가 아니라 진단 숫자에서 규칙으로 만든다 (AI 호출·비용이 늘지 않음)
import React from "react";

// 노출률 등급: 해외 GEO 측정 가이드(texta.ai)의 참고 기준. 25% 미만 약함, 50% 미만 보통, 그 이상 강함
const GRADES = [
  { max: 25, name: "약함", className: "bad" },
  { max: 50, name: "보통", className: "warn" },
  { max: Infinity, name: "강함", className: "good" },
];
export function gradeOf(rate) {
  if (typeof rate !== "number") return null;
  return GRADES.find((g) => rate < g.max);
}

// 받침이 있으면 앞 조사(이·을), 없으면 뒤 조사(가·를). 한글이 아닌 글자로 끝나면 받침 없음으로 봄
export function josa(word, withBatchim, without) {
  const code = String(word).trim().slice(-1).charCodeAt(0) - 0xac00;
  const hasBatchim = code >= 0 && code <= 11171 && code % 28 !== 0;
  return `${word}${hasBatchim ? withBatchim : without}`;
}

// 가게 이름 비교용: 띄어쓰기·대소문자 무시 ("바삭 공방" = "바삭공방")
const keyOf = (name) => String(name || "").replace(/\s/g, "").toLowerCase();

// 도넛: 같은 원을 여러 번 겹쳐 그리고, 원마다 테두리를 "자기 몫(둘레 × 비율)"만큼만 칠한다
export function Ring({ parts, size = 132, stroke = 22, track = "#ffffff" }) {
  const r = (size - stroke) / 2;
  const C = 2 * Math.PI * r;                                    // 원 둘레
  const total = parts.reduce((sum, p) => sum + p.value, 0) || 1;
  let start = 0;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="rp-ring" role="img" aria-label={parts.map((p) => `${p.label} ${p.value}`).join(", ")}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={track} strokeWidth={stroke} />
      {parts.map((p) => {
        const length = C * (p.value / total);                    // 이 조각이 칠할 길이
        const arc = (
          <circle key={p.label} cx={size / 2} cy={size / 2} r={r} fill="none" stroke={p.color} strokeWidth={stroke}
            strokeDasharray={`${length} ${C - length}`} strokeDashoffset={-start}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}>   {/* 12시 방향에서 시작 */}
            <title>{`${p.label} ${p.value}`}</title>
          </circle>
        );
        start += length;
        return arc;
      })}
    </svg>
  );
}

// 가로 막대 목록: 칸 너비 = 값 ÷ 기준값
function Bars({ rows, max }) {
  return (
    <div className="rp-bars">
      {rows.map((row) => (
        <div className={row.low ? "rp-bar low" : "rp-bar"} key={row.label}>
          <span>{row.label}</span>
          <div className="rp-track"><div style={{ width: `${max ? Math.min(100, (row.value / max) * 100) : 0}%`, background: row.color }} /></div>
          <b>{row.text ?? row.value}</b>
        </div>
      ))}
    </div>
  );
}

function Tile({ size, kicker, title, children }) {
  return (
    <article className={`rp-tile ${size}`}>
      <p className="rp-kicker">{kicker}</p>
      <h3>{title}</h3>
      {children}
    </article>
  );
}

// ---------- 맨 위 요약 띠 ----------
export function ReportHero({ report }) {
  const summary = report.summary || {};
  const mention = summary.mention || {};
  const { rate, valid = 0, mentioned = 0 } = mention;
  const grade = gradeOf(rate);
  const average = summary.rank?.average;

  // 결론 한 문장: 10% 이상이면 "10번 중 N번", 그보다 적으면 실제 개수로 (반올림으로 0번이 되지 않게)
  let headline;
  if (!valid) headline = <>AI 답변을 충분히 받지 못해<br />결과를 계산하지 못했어요</>;
  else if (!mentioned) headline = <>손님이 AI에게 맛집을 물으면<br />아직 우리 가게가 <em>나오지 않아요</em></>;
  else if (rate >= 10) headline = <>손님이 AI에게 맛집을 물으면<br />10번 중 <em>{Math.round(rate / 10)}번</em> 우리 가게가 나와요</>;
  else headline = <>손님이 AI에게 맛집을 물으면<br />답변 {valid}개 중 <em>{mentioned}개</em>에서 우리 가게가 나와요</>;

  return (
    <section className="rp-hero">
      <p className="rp-eyebrow">{report.input?.store} · AI 점검 리포트</p>
      <h1>{headline}</h1>
      <div className="rp-stats">
        <div className="rp-stat main">
          <p>AI 노출률</p>
          <strong>{rate ?? "—"}<small>%</small>{grade && <span className={`rp-grade ${grade.className}`}>{grade.name}</span>}</strong>
        </div>
        <div className="rp-stat">
          <p>나올 때 평균 순위</p>
          <strong>{average ?? "—"}{average != null && <small>위</small>}</strong>
        </div>
        <div className="rp-stat">
          <p>받은 AI 답변</p>
          <strong>{valid}<small>개</small></strong>
        </div>
      </div>
      {summary.low_reliability && (
        <p className="rp-warn"><b>신뢰도 낮음</b> · 정상적으로 받은 AI 답변이 충분하지 않아 결과가 실제와 다를 수 있어요. 참고 자료로만 봐 주세요.</p>
      )}
      <p className="rp-note">{report.notice || "AI가 생성한 추정치입니다."}</p>
    </section>
  );
}

// ---------- 한눈에 보기 (카드 7개) ----------
export function ReportOverview({ report, rows }) {
  const summary = report.summary || {};
  const mention = summary.mention || {};
  const { rate, valid = 0, mentioned = 0 } = mention;
  const grade = gradeOf(rate);
  const okAnswers = (report.answers || []).filter((a) => a.status === "ok");
  const dong = report.input?.dong || "";

  // 1) 점유율: 우리 가게 + 함께 많이 나온 가게 3곳 + 그 밖의 가게 (모두 "나온 답변 수" 기준)
  const competitors = (summary.competitors || []).slice(0, 3);
  const usKey = keyOf(report.input?.store);
  let otherAppearances = 0;                                     // 답변마다 다른 가게가 몇 곳 나왔나 (같은 답변 안 중복 제외)
  okAnswers.forEach((a) => {
    const seen = new Set((a.other_stores || []).map((s) => keyOf(s.name)).filter((k) => k && k !== usKey));
    otherAppearances += seen.size;
  });
  const topSum = competitors.reduce((sum, c) => sum + (c.answers || 0), 0);
  const grey = ["#b0b8c1", "#d1d6db", "#e5e8eb"];
  const share = [
    { label: "우리 가게", value: mentioned, color: "#6655db", us: true },
    ...competitors.map((c, i) => ({ label: c.name, value: c.answers || 0, color: grey[i] })),
    { label: "그 밖의 가게", value: Math.max(0, otherAppearances - topSum), color: "#eef0f3" },
  ].filter((p) => p.us || p.value > 0);
  const shareTotal = share.reduce((sum, p) => sum + p.value, 0);
  const top = competitors[0];
  let shareTitle;
  if (!top) shareTitle = "함께 나온 다른 가게가 없어요";
  else if (mentioned >= (top.answers || 0)) shareTitle = <><b>우리 가게</b>가 가장 많이 나왔어요</>;
  else if (!mentioned) shareTitle = <><b className="bad">{josa(top.name, "이", "가")}</b> 가장 많이 나왔어요</>;
  else {
    const times = Math.round((top.answers || 0) / mentioned);
    shareTitle = times >= 2
      ? <><b className="bad">{josa(top.name, "이", "가")}</b> 우리보다 {times}배 많이 나왔어요</>
      : <><b className="bad">{josa(top.name, "이", "가")}</b> 우리보다 조금 더 많이 나왔어요</>;
  }

  // 1-2) AI가 우리 가게를 소개한 말: 가장 많이 쓴 소개 문장 3개 (서버가 셈)
  const quotes = (summary.descriptions || []).slice(0, 3);

  // 2) 순위 분포: 여러 가게를 나열한 답변에서 몇 번째였나
  const ranked = okAnswers.filter((a) => a.mentioned);
  const rankRows = [
    { label: "1위", value: ranked.filter((a) => a.rank === 1).length },
    { label: "2~3위", value: ranked.filter((a) => a.rank === 2 || a.rank === 3).length },
    { label: "4위 이하", value: ranked.filter((a) => a.rank >= 4).length },
    { label: "순위 없음", value: ranked.filter((a) => typeof a.rank !== "number").length },   // 한 곳만 소개한 답변
    { label: "안 나옴", value: valid - ranked.length, color: "#d1d6db" },
  ].filter((r) => r.label !== "순위 없음" || r.value > 0);
  const average = summary.rank?.average;
  const rankTitle = average != null ? <>나올 때는 평균 <b>{average}위</b>예요</>
    : mentioned ? "목록이 아닌 답변에서만 나왔어요" : "아직 순위에 오르지 못했어요";

  // 3) 분위기: 우리 가게가 나온 답변에서 AI가 어떤 말투로 소개했나
  const sentiment = summary.sentiment || {};
  const pos = sentiment["긍정"] || 0, neu = sentiment["중립"] || 0, neg = sentiment["부정"] || 0;
  const sentTotal = pos + neu + neg;
  const sentTitle = !sentTotal ? "소개된 답변이 없어 분위기를 알 수 없어요"
    : neg ? <>나쁘게 소개한 답변이 <b className="bad">{neg}개</b> 있어요</>
    : pos === sentTotal ? <>나온 답변은 모두 <b>좋게</b> 소개했어요</>
    : <>좋게 소개한 답변이 <b>{Math.round((pos / sentTotal) * 100)}%</b>예요</>;

  // 4) 출처 종류: AI가 참고한 사이트를 블로그·지도 등으로 나눔 (서버가 분류해서 줌)
  const kinds = Object.entries(summary.sources?.kinds || {}).sort((a, b) => b[1] - a[1]);
  const srcTotal = summary.sources?.total || kinds.reduce((sum, [, n]) => sum + n, 0);
  const [topKind, topKindCount] = kinds[0] || [];
  const srcTitle = !srcTotal ? "AI가 출처를 남기지 않았어요"
    : topKind === "기타" ? "여러 사이트를 고루 참고했어요"
    : <><b>{josa(topKind, "을", "를")}</b> 가장 많이 봤어요 ({Math.round((topKindCount / srcTotal) * 100)}%)</>;

  // 5) 질문 유형별: 가장 약한 유형을 결론으로
  const types = Object.entries(summary.by_type || {});
  const measured = types.filter(([, v]) => v.valid);
  const rates = measured.map(([, v]) => v.rate ?? 0);
  const weakest = measured.find(([, v]) => (v.rate ?? 0) === Math.min(...rates));
  const typeTitle = !measured.length ? "유형별로 셀 답변이 없어요"
    : Math.max(...rates) === 0 ? "모든 유형에서 아직 나오지 않아요"
    : Math.min(...rates) === Math.max(...rates) ? "유형별로 고르게 나왔어요"
    : <><b className="bad">{weakest[0]}</b> 질문에서 가장 약해요</>;
  const typeMax = Math.max(1, ...measured.map(([, v]) => v.valid));

  // 6) 질문 × 답변 지도: 질문 10개마다 1·2·3번째 답변이 어땠나
  const hitQuestions = rows.filter((q) => q.hit > 0).length;
  const heatTitle = !hitQuestions ? "아직 어떤 질문에서도 나오지 않았어요"
    : hitQuestions === rows.length ? "모든 질문에서 한 번 이상 나왔어요"
    : <>질문 {rows.length}개 중 <b>{hitQuestions}개</b>에서만 우리 가게가 나왔어요</>;
  const half = Math.ceil(rows.length / 2);
  const heatColumn = (list) => (
    <div className="rp-heat">
      <span /><span className="rp-heat-h">1</span><span className="rp-heat-h">2</span><span className="rp-heat-h">3</span>
      {list.map((q) => (
        <React.Fragment key={q.id}>
          <span className="rp-heat-q" title={q.text}>{dong && q.text.startsWith(dong) ? q.text.slice(dong.length).replace(/^에서\s|^\s/, "") || q.text : q.text}</span>
          {[1, 2, 3].map((run) => {
            const a = q.answers.find((x) => x.run === run);
            const state = !a || a.status !== "ok" ? "fail" : a.mentioned ? "hit" : "";
            return <span key={run} className={`rp-cell ${state}`} title={`${run}번째 답변: ${state === "hit" ? "우리 가게 나옴" : state === "fail" ? "답변 실패" : "안 나옴"}`} />;
          })}
        </React.Fragment>
      ))}
    </div>
  );

  return (
    <section className="rp-overview">
      <div className="rp-head"><h2>한눈에 보기</h2><p>AI 답변 {valid}개를 여덟 가지로 나눠 봤어요.</p></div>
      <div className="rp-bento">
        <Tile size="w3" kicker="AI 노출률" title={rate == null ? "노출률을 계산하지 못했어요" : <>노출률 <b>{rate}%</b>, {grade?.name === "강함" ? "잘 나오는 편이에요" : grade?.name === "보통" ? "보통이에요" : "아직 약한 편이에요"}</>}>
          <div className="rp-scale">
            <div className="rp-scale-bar"><span /><span /><span /></div>
            {rate != null && <span className="rp-scale-mark" style={{ left: `${Math.min(100, Math.max(0, rate))}%` }} />}
            <div className="rp-scale-labels"><span>약함 ~25%</span><span>보통 ~50%</span><span>강함 50%~</span></div>
          </div>
          <p className="rp-sub">정상 답변 {valid}개 중 {mentioned}개에서 우리 가게가 나왔어요. 등급은 해외 GEO 측정 가이드의 참고 기준이에요.</p>
        </Tile>

        {/* 카드 이름은 의견 팝업 2번 질문("'AI가 우리 가게를 소개한 말'이 실제 가게와 맞았나요?")과 같게 */}
        <Tile size="w3" kicker="AI가 우리 가게를 소개한 말" title={quotes.length ? "AI는 우리 가게를 이렇게 소개해요" : "AI 답변에서 우리 가게를 소개한 말이 없어요"}>
          {quotes.length > 0 ? (
            <div className="rp-quotes">
              {quotes.map((d) => <p key={d.text}>“{d.text}”<span>{d.count}번</span></p>)}
            </div>
          ) : <p className="rp-sub">{mentioned ? "우리 가게가 나온 답변에 소개 문장이 없었어요." : "우리 가게가 나온 답변이 없어요."}</p>}
        </Tile>

        {/* 카드 이름은 의견 팝업 3번 질문("'AI 답변에 함께 나온 가게'가 실제 경쟁 가게와 비슷했나요?")과 같게 */}
        <Tile size="w6" kicker="AI 답변에 함께 나온 가게 · 점유율" title={shareTitle}>
          <div className="rp-share">
            <div className="rp-row">
              <Ring parts={share} />
              <div className="rp-legend">
                {share.map((p) => (
                  <span key={p.label} className={p.us ? "us" : ""}><i style={{ background: p.color }} />{p.label}<b>{shareTotal ? Math.round((p.value / shareTotal) * 100) : 0}%</b></span>
                ))}
              </div>
            </div>
            {competitors.length > 0 && (
              <ol className="rp-shops">
                {competitors.map((c, i) => (
                  <li key={c.name}>
                    <span className="rp-shop-no" style={{ background: grey[i] }}>{i + 1}</span>
                    <span className="rp-shop-body"><strong>{c.name}</strong><span>{c.description || "소개 문장 없음"}</span></span>
                    <b>답변 {c.answers ?? 0}개</b>
                  </li>
                ))}
              </ol>
            )}
          </div>
        </Tile>

        <Tile size="w2" kicker="몇 번째로 소개됐나" title={rankTitle}><Bars rows={rankRows} max={valid} /></Tile>

        <Tile size="w2" kicker="어떤 분위기로 소개했나" title={sentTitle}>
          <Bars max={sentTotal} rows={[
            { label: "긍정", value: pos, color: "#00a661" },
            { label: "중립", value: neu, color: "#b0b8c1" },
            { label: "부정", value: neg, color: "#f04452" },
          ]} />
        </Tile>

        <Tile size="w2" kicker="AI가 참고한 출처" title={srcTitle}>
          <Bars rows={kinds.slice(0, 5).map(([label, value]) => ({ label, value }))} max={topKindCount || 1} />
        </Tile>

        <Tile size="w2" kicker="질문 유형별" title={typeTitle}>
          <Bars max={typeMax} rows={types.map(([label, v]) => ({
            label, value: v.mentioned || 0, text: v.valid ? `${v.mentioned || 0}/${v.valid}` : "—", low: v.valid > 0 && !v.mentioned,
          }))} />
        </Tile>

        <Tile size="w4" kicker={`질문 ${rows.length}개 × 답변 3번`} title={heatTitle}>
          <div className="rp-heat-wrap">{heatColumn(rows.slice(0, half))}{heatColumn(rows.slice(half))}</div>
          <p className="rp-sub">보라 칸이 우리 가게가 나온 답변이에요. 빗금 칸은 AI가 답하지 못한 경우예요.</p>
        </Tile>
      </div>
    </section>
  );
}
