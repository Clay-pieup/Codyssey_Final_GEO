"""진단 리포트를 메일용 HTML로 만든다 → Make가 Gmail 본문에 그대로 붙인다.

근거: docs/ARCHITECTURE.md 5장 (Make로 보내는 칸 report_html), 진행 기록 10/31 (메일 리포트를 화면과 같은 형식으로)
- 화면(geo_frontend/src/main.jsx)의 결과 리포트와 같은 순서·같은 항목으로 만든다
- 메일 프로그램(Gmail·네이버 메일)은 <style> 묶음, 버튼, 질문 펼치기 같은 움직임을 지우거나 막는다
  → 모양은 태그마다 style="..."로 직접 적고, 칸 나누기는 <table>로 한다 (메일에서 가장 덜 깨지는 방식)
- AI 답변에서 온 글자는 모두 esc()를 거친다 (<, & 같은 기호가 메일 모양을 깨거나 코드로 읽히지 않게)
- 답변 원문 30개는 넣지 않는다 (Gmail은 약 100KB가 넘는 메일을 중간에서 자름) → 질문마다 "3번 중 몇 번 언급"만
"""

import html

SITE_URL = "https://codyssey-final-geo.vercel.app"
SERVICE_NAME = "우리가게 AI 점검"

# 화면(styles.css)과 같은 색
PURPLE, PURPLE_BG, INK, MUTED, LINE, PAGE_BG = "#6655db", "#f0edff", "#20243a", "#7d8397", "#e8eaf2", "#f7f8fc"
GREEN, GREEN_BG, GRAY_BG = "#1f8a52", "#e8f7ef", "#f2f3f7"
FONT = "'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif"


def esc(value) -> str:
    """글자를 메일에 넣어도 안전한 모양으로 바꾼다. 없으면 빈 글자."""
    return html.escape("" if value is None else str(value))


def card(title: str, body: str, note: str = "") -> str:
    """흰 바탕 카드 한 칸 (화면의 result-section). title·note는 코드가 정한 글자만 넣는다."""
    right = f'<td align="right" style="color:{PURPLE};font-size:11px;">{note}</td>' if note else ""
    return (
        f'<tr><td style="padding:0 0 14px;"><table width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:#ffffff;border:1px solid {LINE};border-radius:14px;"><tr><td style="padding:22px;">'
        f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
        f'<td style="font-size:16px;font-weight:700;color:{INK};padding-bottom:12px;">{title}</td>{right}</tr></table>'
        f"{body}</td></tr></table></td></tr>"
    )


def numbered(index: int, title: str, lines: list[str]) -> str:
    """번호 상자 + 굵은 제목 + 설명 줄들 (화면의 recommendation). 글자는 이미 esc()를 거친 것만 받는다."""
    text = "".join(f'<div style="color:{MUTED};font-size:12px;line-height:1.7;">{line}</div>' for line in lines)
    return (
        f'<table width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid {LINE};"><tr>'
        f'<td width="40" valign="top" style="padding:14px 0;"><div style="width:30px;height:30px;line-height:30px;'
        f'text-align:center;border-radius:9px;background:{PURPLE_BG};color:{PURPLE};font-size:11px;font-weight:800;">'
        f'{index:02d}</div></td><td valign="top" style="padding:14px 0;">'
        f'<div style="color:{INK};font-size:14px;font-weight:700;padding-bottom:4px;">{title}</div>{text}</td></tr></table>'
    )


def bar(rate) -> str:
    """언급률 막대. 메일은 그라데이션·움직임을 못 쓰므로 칸 2개(보라·회색)의 너비로 그린다."""
    rate = max(0, min(100, rate if isinstance(rate, (int, float)) else 0))
    filled = f'<td width="{rate}%" style="background:{PURPLE};height:8px;font-size:0;">&nbsp;</td>' if rate > 0 else ""
    empty = f'<td style="background:#f0f1f6;height:8px;font-size:0;">&nbsp;</td>' if rate < 100 else ""
    return f'<table width="100%" cellpadding="0" cellspacing="0" style="border-radius:4px;"><tr>{filled}{empty}</tr></table>'


def question_rows(report: dict) -> list[dict]:
    """질문 10개마다 답변 3개를 묶어 '정상 답변 중 몇 번 언급'을 센다 (화면 questionRows와 같은 규칙)."""
    rows = []
    for q in report.get("questions") or []:
        answers = [a for a in report.get("answers") or [] if a.get("question_id") == q.get("id")]
        valid = [a for a in answers if a.get("status") == "ok"]
        rows.append({"type": q.get("type", ""), "text": q.get("text", ""),
                     "valid": len(valid), "hit": sum(1 for a in valid if a.get("mentioned"))})
    return rows


def build_report_html(report: dict, name: str = "") -> str:
    """리포트(dict) → 메일 본문 HTML 한 덩어리. 화면 리포트의 1~9번 칸을 같은 순서로 만든다."""
    inp = report.get("input") or {}
    summary = report.get("summary") or {}
    mention = summary.get("mention") or {}
    rank = summary.get("rank") or {}
    agent = report.get("agent") or {}
    settings = report.get("settings") or {}
    answers = report.get("answers") or []
    rows = question_rows(report)
    store = esc(inp.get("store"))
    parts = []

    # 머리말: 서비스 이름 + "OO AI 점검 리포트" + 인사
    hello = f"{esc(name)} 사장님, 의견 고맙습니다. " if name else ""
    parts.append(
        f'<tr><td style="padding:4px 0 18px;"><div style="color:{PURPLE};font-size:13px;font-weight:800;">{SERVICE_NAME}</div>'
        f'<div style="color:{INK};font-size:24px;font-weight:800;padding:10px 0 6px;">{store} '
        f'<span style="color:{PURPLE};">AI 점검 리포트</span></div>'
        f'<div style="color:{MUTED};font-size:12px;">{hello}화면에서 보신 진단 리포트를 보내 드려요. AI가 생성한 추정치입니다.</div></td></tr>'
    )

    # 1. 어떻게 점검했나요
    search = " · 웹 검색 사용" if settings.get("use_search") else ""
    facts = [("지역", esc(inp.get("region"))), ("대표 메뉴", esc(", ".join(inp.get("menus") or []))),
             ("물어본 AI", f"Google Gemini ({esc(report.get('model'))}){search}"),
             ("질문 방식", f"손님 말투 질문 {len(rows)}개 × {esc(settings.get('repeat', 3))}번 = 답변 {len(answers)}개")]
    parts.append(card("어떻게 점검했나요", "".join(
        f'<div style="padding:4px 0;"><span style="color:#9297a7;font-size:11px;">{k}</span><br>'
        f'<span style="color:{INK};font-size:13px;font-weight:600;">{v}</span></div>' for k, v in facts)))

    # 2. 핵심 숫자 3개 (화면의 metric-card)
    rate = mention.get("rate")
    metrics = [
        ("우리 가게 언급률", f"{esc(rate) if rate is not None else '—'}%",
         f"정상 답변 {esc(mention.get('valid', 0))}개 중 {esc(mention.get('mentioned', 0))}개에서 언급"),
        ("언급될 때 평균 순위", f"{esc(rank['average'])}위" if rank.get("average") is not None else "—",
         f"여러 가게를 나열한 답변 {esc(rank.get('counted'))}개 기준, 1위 {esc(rank.get('first_place', 0))}번"
         if rank.get("counted") else "순위를 셀 수 없음"),
        ("받은 AI 답변", f"{esc(mention.get('valid', 0))}개", f"전체 {len(answers)}개 중 정상 답변"),
    ]
    cells = "".join(
        f'<td width="33%" valign="top" style="padding:0 4px;"><table width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:#ffffff;border:1px solid {LINE};border-radius:14px;"><tr><td style="padding:16px 12px;">'
        f'<div style="color:{MUTED};font-size:11px;">{label}</div>'
        f'<div style="color:{INK};font-size:26px;font-weight:800;padding:6px 0;">{value}</div>'
        f'<div style="color:#a0a4b2;font-size:10px;line-height:1.5;">{small}</div></td></tr></table></td>'
        for label, value, small in metrics)
    parts.append(f'<tr><td style="padding:0 0 14px;"><table width="100%" cellpadding="0" cellspacing="0" '
                 f'><tr>{cells}</tr></table></td></tr>')
    if summary.get("low_reliability"):
        parts.append(f'<tr><td style="padding:0 0 14px;color:#9a5b00;font-size:12px;"><b>신뢰도 낮음</b> · 정상적으로 받은 '
                     f'AI 답변이 충분하지 않아 결과가 실제와 다를 수 있어요. 참고 자료로만 봐 주세요.</td></tr>')

    # 3. 질문 유형별 결과
    type_rows = ""
    for t, v in (summary.get("by_type") or {}).items():
        count = f"{esc(v.get('valid'))}개 중 {esc(v.get('mentioned', 0))}개" if v.get("valid") else "측정 불가"
        type_rows += (f'<tr><td width="70" style="padding:7px 0;color:{INK};font-size:12px;font-weight:700;">{esc(t)}</td>'
                      f'<td style="padding:7px 10px;">{bar(v.get("rate"))}</td>'
                      f'<td width="70" align="right" style="color:{MUTED};font-size:11px;">{count}</td></tr>')
    parts.append(card("질문 유형별 결과", f'<table width="100%" cellpadding="0" cellspacing="0">{type_rows}</table>',
                      "손님이 어떻게 물을 때 나오나요"))

    # 4. AI에게 물어본 질문 10개 (메일에서는 펼치기가 안 돼 질문과 언급 수만)
    q_rows = ""
    for r in rows:
        badge = f"{r['valid']}번 중 {r['hit']}번 언급" if r["valid"] else "답변 없음"
        color, bg = (GREEN, GREEN_BG) if r["hit"] else ("#8a8fa1", GRAY_BG)  # 한 번이라도 언급되면 초록 배지
        q_rows += (f'<tr><td style="padding:9px 0;border-top:1px solid {LINE};">'
                   f'<span style="padding:2px 6px;border-radius:6px;background:{PURPLE_BG};color:{PURPLE};font-size:10px;'
                   f'font-weight:700;">{esc(r["type"])}</span> <span style="color:{INK};font-size:12px;">{esc(r["text"])}</span></td>'
                   f'<td width="96" align="right" style="padding:9px 0;border-top:1px solid {LINE};">'
                   f'<span style="padding:3px 8px;border-radius:20px;font-size:10px;font-weight:700;background:{bg};color:{color};">'
                   f'{badge}</span></td></tr>')
    parts.append(card(f"AI에게 물어본 질문 {len(rows)}개", f'<table width="100%" cellpadding="0" cellspacing="0">{q_rows}</table>'))

    # 5. AI가 우리 가게를 소개한 말
    quotes = summary.get("descriptions") or []
    body = "".join(f'<div style="color:#252941;font-size:12px;line-height:1.9;">· “{esc(d.get("text"))}” '
                   f'<span style="color:#a0a4b2;font-size:10px;">{esc(d.get("count"))}번</span></div>' for d in quotes)
    parts.append(card("AI가 우리 가게를 소개한 말", body or f'<div style="color:{MUTED};font-size:12px;">AI 답변에서 우리 가게를 소개한 말이 없어요.</div>'))

    # 6. AI 답변에 함께 나온 가게 (상위 3곳)
    shops = (summary.get("competitors") or [])[:3]
    body = "".join(numbered(i, esc(c.get("name")), [esc(c.get("description") or "소개 문장 없음"),
                                                     f"함께 나온 답변 {esc(c.get('answers', 0))}개"])
                   for i, c in enumerate(shops, 1))
    parts.append(card("AI 답변에 함께 나온 가게", body or f'<div style="color:{MUTED};font-size:12px;">함께 나온 다른 가게가 없어요.</div>'))

    # 7. AI 추가 진단 (Agent) — 실행됐을 때만 (화면과 같음)
    if agent.get("ran"):
        how = "더 자세히 진단하기" if agent.get("trigger") == "button" else "언급률이 낮아 자동 실행"
        body = f'<div style="color:{MUTED};font-size:12px;padding-bottom:6px;">{esc(agent.get("reason_to_run"))}</div>'
        body += "".join(numbered(i, esc(t.get("tool_label") or "추가 진단"), [
            f"추가 질문: “{esc(t.get('question'))}”",
            f"AI가 이 질문을 고른 이유: {esc(t.get('why') or '별도 설명 없음')}",
            f"결과: 정상 답변 {esc((t.get('result') or {}).get('valid', 0))}개 중 "
            f"{esc((t.get('result') or {}).get('mentioned', 0))}개에서 언급"]) for i, t in enumerate(agent.get("trace") or [], 1))
        parts.append(card("AI 추가 진단", body, how))

    # 8. 개선 제안 (3개)
    tips = (report.get("suggestions") or [])[:3]
    body = "".join(numbered(i, esc(s.get("title")), [esc(s.get("detail"))] +
                            ([f"근거: {esc(s.get('evidence'))}"] if s.get("evidence") else []))
                   for i, s in enumerate(tips, 1))
    parts.append(card("개선 제안", body or f'<div style="color:{MUTED};font-size:12px;">개선 제안을 만들지 못했어요.</div>', "근거는 위 진단 결과"))

    # 9. 안내 + 다시 점검하기
    parts.append(card("안내", f'<div style="color:{MUTED};font-size:12px;line-height:1.8;">{esc(report.get("notice"))}<br>'
                      f'답변 원문은 메일에 넣지 않았어요. 언제든 다시 점검할 수 있어요: '
                      f'<a href="{SITE_URL}" style="color:{PURPLE};">{SITE_URL}</a></div>'))

    return (
        f'<div style="margin:0;padding:24px 12px;background:{PAGE_BG};font-family:{FONT};">'
        f'<table width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;margin:0 auto;">'
        f'{"".join(parts)}'
        f'<tr><td style="padding:6px 0;color:#a0a4b2;font-size:10px;">{SERVICE_NAME} · AI가 생성한 추정치 · 실제 AI 앱 답변과 다를 수 있음</td></tr>'
        f"</table></div>"
    )
