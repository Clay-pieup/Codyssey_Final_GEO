// ---------- 결과 리포트: AI에게 물어본 질문 (리포트 개편 단위 4, 10/31 팀장 결정) ----------
// 요약 먼저(판정 한 줄 + AI가 소개한 가게 순서 + 우리 가게 소개) → 그 아래 원문을 기호 없이 정리
// 우리 가게가 나온 답변만 원문을 펼쳐 두고, 안 나온 답변은 접어 둔다
// 원문 정리는 새 라이브러리 없이: 줄 맨 앞 기호(###, *, 1.)만 보고 제목·목록으로 나누고, 글자는 React가 안전하게 넣는다
import React, { useState } from "react";
import { ChevronDown } from "lucide-react";

const keyOf = (name) => String(name || "").replace(/\s/g, "").toLowerCase();

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

// 원문에서 강조할 우리 가게 이름: 전체 이름 + 지점명을 뺀 앞 단어 ("초록별돈까스 망원점" → "초록별돈까스")
function storeWords(store) {
  const full = String(store || "").trim();
  const head = full.split(/\s+/)[0];
  return [full, head].filter((w, i, all) => w.length >= 2 && all.indexOf(w) === i).sort((a, b) => b.length - a.length);
}

// 한 줄 안의 꾸밈: [글자](주소) → 글자만, **굵게** → 굵게, 우리 가게 이름 → 보라 강조
function Inline({ text, words }) {
  const plain = String(text).replace(/\[([^\]]+)\]\([^)]*\)/g, "$1");
  const pattern = words.length ? new RegExp(`(${words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`) : null;
  const mark = (segment, key) => {
    if (!pattern) return segment;
    return segment.split(pattern).map((part, i) => (i % 2 ? <mark key={`${key}-${i}`}>{part}</mark> : part));
  };
  return plain.split(/\*\*(.+?)\*\*/).map((part, i) => {
    const content = mark(part.replace(/\*\*/g, ""), i);
    return i % 2 ? <strong key={i}>{content}</strong> : <React.Fragment key={i}>{content}</React.Fragment>;
  });
}

// 원문 → 블록 목록. 블록 종류: 문단(p), 가게 카드(store: 제목 + 항목), 목록(list)
// "### 1. 가게"가 나오면 가게 카드를 열고, 그 아래 "* 대표 메뉴: …" 줄을 카드 안 항목으로 넣는다
export function parseAnswer(text) {
  const blocks = [];
  let open = null;                                                      // 지금 항목을 받고 있는 가게 카드 또는 목록
  for (const raw of String(text || "").replace(/\r/g, "").split("\n")) {
    const line = raw.trim();
    if (!line) { if (open?.kind === "list") open = null; continue; }   // 빈 줄: 목록은 끝, 가게 카드는 다음 제목까지 유지
    if (/^([-*_]\s*){3,}$/.test(line)) { open = null; continue; }      // 구분선(---)은 지움
    const heading = line.match(/^#{1,6}\s+(.*)$/);
    if (heading) {
      open = { kind: "store", title: heading[1].replace(/\*\*/g, ""), items: [] };
      blocks.push(open);
      continue;
    }
    const bullet = line.match(/^(?:[*•-]|\d+[.)])\s+(.*)$/);
    if (bullet) {
      // "**대표 메뉴:** 값" 또는 "대표 메뉴: 값"은 이름·값 두 칸으로
      const pair = bullet[1].match(/^\*\*([^*]{1,12}?)\s*[:：]\s*\*\*\s*(.*)$/)    // **이름:** 값
        || bullet[1].match(/^\*\*([^*]{1,12})\*\*\s*[:：]\s*(.+)$/)                       // **이름**: 값
        || bullet[1].match(/^([^:*：]{1,10})\s*[:：]\s*(.+)$/);                          // 이름: 값
      const item = pair ? { name: pair[1].trim(), value: pair[2] } : { value: bullet[1] };
      if (open?.kind !== "store" && open?.kind !== "list") { open = { kind: "list", items: [] }; blocks.push(open); }
      open.items.push(item);
      continue;
    }
    if (open?.kind === "store") { open.items.push({ value: line }); continue; }   // 가게 제목 아래 설명 문장
    open = null;
    blocks.push({ kind: "p", text: line });
  }
  return blocks;
}

function PrettyAnswer({ text, words }) {
  const blocks = parseAnswer(text);
  const isUs = (title) => words.some((w) => title.includes(w));
  const items = (list) => (
    <ul>
      {list.map((it, i) => (
        <li key={i} className={it.name ? "" : "plain"}>
          {it.name && <span className="rq-k">{it.name}</span>}
          <span><Inline text={it.value} words={words} /></span>
        </li>
      ))}
    </ul>
  );
  return (
    <div className="rq-md">
      {blocks.map((b, i) => {
        if (b.kind === "store") {
          return (
            <div key={i} className={isUs(b.title) ? "rq-store us" : "rq-store"}>
              <h5><Inline text={b.title} words={[]} />{isUs(b.title) && <em>우리 가게</em>}</h5>
              {b.items.length > 0 && items(b.items)}
            </div>
          );
        }
        if (b.kind === "list") return <div key={i} className="rq-list">{items(b.items)}</div>;
        return <p key={i}><Inline text={b.text} words={words} /></p>;
      })}
    </div>
  );
}

// 이 답변에서 AI가 소개한 가게 순서: 다른 가게 목록에 우리 가게를 순위 자리에 끼워 넣는다 (순위가 없으면 맨 앞)
function orderOf(answer, store) {
  const usKey = keyOf(store);
  const list = (answer.other_stores || []).map((s) => s.name).filter((n) => n && keyOf(n) !== usKey);
  if (answer.mentioned) {
    const at = typeof answer.rank === "number" ? Math.min(answer.rank - 1, list.length) : 0;
    list.splice(at, 0, null);                                           // null = 우리 가게 자리
  }
  return list;
}

function AnswerCard({ answer, store, words, open, onFold }) {
  if (!answer || answer.status !== "ok") {
    return (
      <div className="rq-ans">
        <p className="rq-verdict miss">이 답변은 <b>받지 못했어요</b></p>
        <p className="rq-sub">AI 응답이 실패해 노출률 계산에서 뺐어요.</p>
      </div>
    );
  }
  const order = orderOf(answer, store);
  const sites = siteNames(answer);
  return (
    <div className="rq-ans">
      <p className={answer.mentioned ? "rq-verdict" : "rq-verdict miss"}>
        {answer.mentioned
          ? (typeof answer.rank === "number" ? <>우리 가게가 <b>{answer.rank}번째</b>로 나왔어요</> : <>우리 가게가 <b>나왔어요</b></>)
          : <>이 답변에는 우리 가게가 <b>없어요</b></>}
      </p>
      {order.length > 0 && (
        <div className="rq-order">
          <span className="rq-label">AI가 소개한 순서</span>
          <div className="rq-chips">
            {order.map((name, i) => (
              <span key={i} className={name === null ? "rq-chip us" : "rq-chip"}><b>{i + 1}</b>{name === null ? "우리 가게" : name}</span>
            ))}
          </div>
        </div>
      )}
      {answer.mentioned && answer.description && (
        <p className="rq-said">AI가 우리 가게를 이렇게 소개했어요 · <b>"{answer.description}"</b></p>
      )}
      {answer.text && (
        <div className="rq-orig">
          <div className="rq-orig-head">
            <span className="rq-label">AI 답변 원문{!answer.mentioned && !open ? " (우리 가게가 없어 접어 뒀어요)" : ""}</span>
            <button type="button" className="rq-fold" aria-expanded={open} onClick={onFold}>{open ? "접기" : "펼치기"}</button>
          </div>
          {open && <PrettyAnswer text={answer.text} words={words} />}
          {open && sites.length > 0 && <p className="rq-sources">출처: {sites.slice(0, 5).join(", ")}</p>}
        </div>
      )}
    </div>
  );
}

export function ReportQuestions({ report, rows }) {
  const store = report.input?.store || "";
  const words = storeWords(store);
  const firstHit = rows.find((q) => q.hit > 0);
  const [openQuestion, setOpenQuestion] = useState(firstHit ? firstHit.id : null);   // 우리 가게가 나온 첫 질문은 펼친 채로 시작
  const [tabOf, setTabOf] = useState({});                                           // 질문마다 고른 회차
  const [foldOf, setFoldOf] = useState({});                                         // 원문을 직접 펼치거나 접은 기록

  return (
    <section className="rq">
      <div className="rp-head"><h2>AI에게 물어본 질문</h2><p>우리 가게가 나온 답변은 원문까지 펼쳐 두고, 안 나온 답변은 접어 뒀어요.</p></div>
      <div className="rq-list-wrap">
        {rows.map((q) => {
          const isOpen = openQuestion === q.id;
          const answers = [...q.answers].sort((a, b) => a.run - b.run);
          const defaultRun = (answers.find((a) => a.status === "ok" && a.mentioned) || answers[0])?.run;
          const run = tabOf[q.id] ?? defaultRun;
          const answer = answers.find((a) => a.run === run);
          const foldKey = `${q.id}-${run}`;
          const originalOpen = foldOf[foldKey] ?? Boolean(answer?.mentioned);  // 기본: 우리 가게가 나온 답변만 펼침
          return (
            <div className={isOpen ? "rq-item open" : "rq-item"} key={q.id}>
              <button type="button" className="rq-row" aria-expanded={isOpen} onClick={() => setOpenQuestion(isOpen ? null : q.id)}>
                <span className="rq-type">{q.type}</span>
                <span className="rq-text">{q.text}</span>
                <span className={q.hit > 0 ? "rq-badge hit" : "rq-badge"}>{q.valid ? `${q.valid}번 중 ${q.hit}번 나옴` : "답변 없음"}</span>
                <ChevronDown size={18} className="rq-chev" />
              </button>
              {isOpen && (
                <div className="rq-body">
                  <div className="rq-tabs" role="tablist">
                    {answers.map((a) => (
                      <button type="button" role="tab" key={a.run} aria-selected={a.run === run} onClick={() => setTabOf((old) => ({ ...old, [q.id]: a.run }))}>
                        {a.run}번째 답변{a.status === "ok" && a.mentioned && <span className="rq-dot" title="우리 가게 나옴" />}
                      </button>
                    ))}
                  </div>
                  <AnswerCard answer={answer} store={store} words={words} open={originalOpen}
                    onFold={() => setFoldOf((old) => ({ ...old, [foldKey]: !originalOpen }))} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
