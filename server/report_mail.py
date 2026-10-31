"""진단 리포트를 메일용 HTML로 만든다 → Make가 Gmail 본문에 그대로 붙인다.

근거: docs/ARCHITECTURE.md 5장 (Make로 보내는 칸 report_html), 진행 기록 10/31·11/1 (리포트 개편 단위 5: 메일도 새 화면에 맞춤)
- 화면 결과 리포트와 같은 순서·같은 문장 규칙으로 만든다
  요약 띠(ReportDashboard.jsx) → 한눈에 보기 8칸 → 질문 10개(ReportQuestions.jsx) → AI 추가 진단(ReportAgent.jsx)
  → 개선 제안(ReportSuggestions.jsx) → 안내
- 메일 프로그램(Gmail·네이버 메일)은 그림(SVG), 버튼, 펼치기, <style> 묶음을 지우거나 막는다
  → 도넛 대신 한 줄짜리 나눔 막대. 모든 그림은 <table> 칸의 너비·색으로, 꾸밈은 태그마다 style="..."로
  → 카드는 한 줄에 하나씩 (휴대폰 메일 앱에서도 깨지지 않게)
- 답변 원문 30개는 넣지 않는다 (Gmail은 약 100KB가 넘는 메일을 중간에서 자름) → 질문마다 "3번 중 몇 번"과 답변 칸 3개만
- AI 답변에서 온 글자는 모두 esc()를 거친다 (<, & 같은 기호가 메일 모양을 깨거나 코드로 읽히지 않게)
"""

import html
import math
import re

SITE_URL = "https://codyssey-final-geo.vercel.app"
SERVICE_NAME = "우리가게 AI 점검"

# 화면(styles.css의 rp-·rq-·ra- 칸)과 같은 색
PURPLE, PURPLE_SOFT, PURPLE_INK = "#6655db", "#ebe8ff", "#5341c9"
INK, SUB, MUTE = "#191f28", "#4e5968", "#8b95a1"
PAGE, HERO, CARD, WHITE = "#ffffff", "#f4f3f8", "#f3f3f7", "#ffffff"
RED, RED_SOFT, GREEN, GREEN_SOFT, WARN, WARN_SOFT = "#f04452", "#ffeeee", "#00a661", "#e3f7ed", "#b77a00", "#fff4dc"
GREYS = ["#b0b8c1", "#d1d6db", "#e5e8eb"]
OTHER = "#eef0f3"
TAG_COLORS = ["#6655db", "#3f8fd0", "#e08a3c"]
FONT = "'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif"
TABLE = 'width="100%" cellpadding="0" cellspacing="0" role="presentation"'

# 노출률 등급: 해외 GEO 측정 가이드(texta.ai)의 참고 기준 (화면 ReportDashboard.jsx GRADES와 같음)
GRADES = [(25, "약함", RED, RED_SOFT), (50, "보통", WARN, WARN_SOFT), (math.inf, "강함", GREEN, GREEN_SOFT)]

# AI 추가 진단의 질문 도구 3개 (화면 ReportAgent.jsx TOOLS와 같음)
TOOLS = {
    "직접 지명형": ("가게 이름을 넣어 물어봐서, AI가 우리 가게를 아는지 확인해요.",
                "가게 이름으로 물으면 AI가 우리 가게를 알아요", "가게 이름으로 물어도 AI가 우리 가게를 잘 몰라요"),
    "경쟁 비교형": ("함께 자주 나온 가게들과 비교하게 물어봐서, 우리 가게의 위치를 확인해요.",
                "다른 가게와 비교할 때도 우리 가게가 나와요", "다른 가게와 비교할 때는 우리 가게가 빠져요"),
    "상황 세분형": ("혼밥·데이트처럼 상황을 더 좁혀 물어봐서, 어떤 상황에서 나오는지 확인해요.",
                "상황을 좁혀 물으면 우리 가게가 나와요", "상황을 좁혀 물어도 우리 가게가 나오지 않아요"),
}


# ---------------------------------------------------------------- 작은 도구

def esc(value) -> str:
    """글자를 메일에 넣어도 안전한 모양으로 바꾼다. 없으면 빈 글자."""
    return html.escape("" if value is None else str(value))


def jsround(x: float) -> int:
    """화면(JavaScript Math.round)과 같은 반올림. 파이썬 round(2.5)는 2라서 화면 숫자와 달라질 수 있음"""
    return int(math.floor(x + 0.5))


def pct(part, whole) -> int:
    return jsround(part / whole * 100) if whole else 0


def josa(word: str, with_batchim: str, without: str) -> str:
    """받침이 있으면 앞 조사(이·을·과), 없으면 뒤 조사(가·를·와). 화면 josa()와 같은 규칙"""
    w = str(word).strip()
    code = ord(w[-1]) - 0xAC00 if w else -1
    has_batchim = 0 <= code <= 11171 and code % 28 != 0
    return w + (with_batchim if has_batchim else without)


def key_of(name) -> str:
    """가게 이름 비교용: 띄어쓰기·대소문자 무시"""
    return re.sub(r"\s", "", str(name or "")).lower()


def grade_of(rate):
    if not isinstance(rate, (int, float)):
        return None
    return next(g for g in GRADES if rate < g[0])


def b(text: str, color: str = PURPLE) -> str:
    """결론 문장 속 강조 (화면 h3 b)"""
    return f'<span style="color:{color};">{text}</span>'


def section_head(title: str, sub: str = "") -> str:
    sub_html = f'<div style="color:{SUB};font-size:13px;padding-top:4px;">{sub}</div>' if sub else ""
    return (f'<tr><td style="padding:34px 0 14px;"><div style="color:{INK};font-size:21px;font-weight:800;letter-spacing:-0.5px;">'
            f'{title}</div>{sub_html}</td></tr>')


def card(kicker: str, title: str, body: str, bg: str = CARD) -> str:
    """회색 카드 한 장 (화면 rp-tile): 작은 이름 + 한 줄 결론 + 그림. kicker·title은 코드가 만든 글자(가게 이름은 esc 후)만"""
    return (f'<tr><td style="padding:0 0 12px;"><table {TABLE} style="background:{bg};border-radius:20px;"><tr><td style="padding:22px;">'
            f'<div style="color:{MUTE};font-size:12px;font-weight:700;">{kicker}</div>'
            f'<div style="color:{INK};font-size:17px;font-weight:800;line-height:1.45;padding:6px 0 14px;">{title}</div>'
            f'{body}</td></tr></table></td></tr>')


def bar_cell(percent: float, color: str, track: str = WHITE, height: int = 10) -> str:
    """막대 하나: 표 한 줄을 색칠한 칸(너비 = 비율)과 빈칸으로 나눈다"""
    p = max(0, min(100, percent))
    filled = f'<td width="{p:.0f}%" style="background:{color};height:{height}px;font-size:0;line-height:0;">&nbsp;</td>' if p > 0 else ""
    empty = f'<td style="background:{track};height:{height}px;font-size:0;line-height:0;">&nbsp;</td>' if p < 100 else ""
    return f'<table {TABLE} style="border-radius:5px;"><tr>{filled}{empty}</tr></table>'


def bars(rows: list[dict], top: float) -> str:
    """이름 · 막대 · 값 목록 (화면 Bars). rows: {"label", "value", "text"?, "color"?, "low"?}"""
    out = ""
    for r in rows:
        color = RED if r.get("low") else r.get("color", PURPLE)
        out += (f'<tr><td width="76" style="padding:5px 0;color:{SUB};font-size:12px;">{esc(r["label"])}</td>'
                f'<td style="padding:5px 10px;">{bar_cell(r["value"] / top * 100 if top else 0, color)}</td>'
                f'<td width="44" align="right" style="color:{INK};font-size:12px;font-weight:700;">{esc(r.get("text", r["value"]))}</td></tr>')
    return f'<table {TABLE}>{out}</table>'


def tag(no, color: str) -> str:
    """번호 칩 (화면 rp-tag)"""
    return (f'<span style="display:inline-block;width:22px;height:22px;line-height:22px;text-align:center;border-radius:7px;'
            f'background:{color};color:#ffffff;font-size:12px;font-weight:800;">{no}</span>')


def white_box(inner: str) -> str:
    return f'<table {TABLE} style="background:{WHITE};border-radius:14px;margin-top:8px;"><tr><td style="padding:12px 14px;">{inner}</td></tr></table>'


# ---------------------------------------------------------------- 리포트에서 숫자 꺼내기 (화면과 같은 규칙)

def question_rows(report: dict) -> list[dict]:
    """질문 10개마다 답변 3개를 묶어 '정상 답변 중 몇 번 언급'과 회차별 상태(hit/miss/fail)를 센다"""
    rows = []
    for q in report.get("questions") or []:
        answers = sorted((a for a in report.get("answers") or [] if a.get("question_id") == q.get("id")), key=lambda a: a.get("run", 0))
        valid = [a for a in answers if a.get("status") == "ok"]
        states = ["fail" if a.get("status") != "ok" else "hit" if a.get("mentioned") else "miss" for a in answers]
        rows.append({"type": q.get("type", ""), "text": q.get("text", ""), "valid": len(valid),
                     "hit": sum(1 for a in valid if a.get("mentioned")), "states": states})
    return rows


def share_of(report: dict) -> tuple[list[dict], dict | None]:
    """점유율: 우리 가게 + 함께 많이 나온 3곳 + 그 밖의 가게 (모두 '나온 답변 수'). 화면 ReportOverview와 같음"""
    summary = report.get("summary") or {}
    mentioned = (summary.get("mention") or {}).get("mentioned") or 0
    competitors = (summary.get("competitors") or [])[:3]
    us_key = key_of((report.get("input") or {}).get("store"))
    other = 0
    for a in report.get("answers") or []:
        if a.get("status") == "ok":
            other += len({key_of(s.get("name")) for s in a.get("other_stores") or [] if key_of(s.get("name")) and key_of(s.get("name")) != us_key})
    top_sum = sum(c.get("answers") or 0 for c in competitors)
    parts = [{"label": "우리 가게", "value": mentioned, "color": PURPLE, "us": True}]
    parts += [{"label": c.get("name", ""), "value": c.get("answers") or 0, "color": GREYS[i]} for i, c in enumerate(competitors)]
    parts.append({"label": "그 밖의 가게", "value": max(0, other - top_sum), "color": OTHER})
    return [p for p in parts if p.get("us") or p["value"] > 0], (competitors[0] if competitors else None)


def weak_spots(report: dict) -> list[dict]:
    """약한 곳: 질문 유형별 + 추가 질문(Agent) + 가장 많이 나온 가게와 비교. 비율 낮은 순 (화면 ReportSuggestions와 같음)"""
    summary = report.get("summary") or {}
    spots = []
    for t, v in (summary.get("by_type") or {}).items():
        if v.get("valid"):
            spots.append({"label": f"{t} 질문", "hit": v.get("mentioned") or 0, "of": v["valid"], "words": [t]})
    for t in (report.get("agent") or {}).get("trace") or []:
        r = t.get("result") or {}
        if r.get("valid") and t.get("tool_label"):
            spots.append({"label": f"추가 질문 · {t['tool_label']}", "hit": r.get("mentioned") or 0, "of": r["valid"], "words": [t["tool_label"]]})
    top = (summary.get("competitors") or [None])[0]
    ours = (summary.get("mention") or {}).get("mentioned") or 0
    if top and (top.get("answers") or 0) > ours:
        spots.append({"label": f"{josa(top.get('name', ''), '과', '와')} 비교", "hit": ours, "of": top["answers"],
                      "words": [top.get("name", "")], "text": f"{ours} : {top['answers']}"})
    return sorted(spots, key=lambda s: s["hit"] / s["of"])


def link_of(suggestion: dict, spots: list[dict]) -> int:
    """근거 문장(없으면 제목·설명)에 약한 곳 이름이 있으면 그 약한 곳 번호. 없으면 -1"""
    for field in (suggestion.get("evidence") or "", f"{suggestion.get('title', '')} {suggestion.get('detail', '')}"):
        for i, spot in enumerate(spots):
            if any(w and w in field for w in spot["words"]):
                return i
    return -1


def numbers_of(evidence: str, spot: dict | None):
    """근거 문장 속 '9개 중 2개' → (2, 9). 없으면 이어진 약한 곳의 숫자"""
    m = re.search(r"(\d+)\s*개[^0-9]{0,6}?중\s*(\d+)\s*개", evidence or "")
    if m and int(m.group(1)) > 0:
        return int(m.group(2)), int(m.group(1))
    return (spot["hit"], spot["of"]) if spot else None


# ---------------------------------------------------------------- 칸 만들기

def hero(report: dict, name: str) -> str:
    summary = report.get("summary") or {}
    mention = summary.get("mention") or {}
    rate, valid, hit = mention.get("rate"), mention.get("valid") or 0, mention.get("mentioned") or 0
    avg = (summary.get("rank") or {}).get("average")
    em = lambda t: f'<span style="color:{PURPLE};">{t}</span>'  # noqa: E731
    if not valid:
        headline = "AI 답변을 충분히 받지 못해<br>결과를 계산하지 못했어요"
    elif not hit:
        headline = f"손님이 AI에게 맛집을 물으면<br>아직 우리 가게가 {em('나오지 않아요')}"
    elif rate >= 10:
        headline = f"손님이 AI에게 맛집을 물으면<br>10번 중 {em(str(jsround(rate / 10)) + '번')} 우리 가게가 나와요"
    else:
        headline = f"손님이 AI에게 맛집을 물으면<br>답변 {valid}개 중 {em(str(hit) + '개')}에서 우리 가게가 나와요"
    g = grade_of(rate)
    grade_html = (f' <span style="display:inline-block;vertical-align:middle;padding:2px 8px;border-radius:7px;background:{g[3]};'
                  f'color:{g[2]};font-size:12px;font-weight:800;">{g[1]}</span>') if g else ""
    stat = lambda label, value, unit, color=INK: (  # noqa: E731
        f'<td width="33%" valign="top" style="padding:0 4px;"><table {TABLE} style="background:{WHITE};border-radius:14px;"><tr>'
        f'<td style="padding:14px 14px 12px;"><div style="color:{MUTE};font-size:12px;">{label}</div>'
        f'<div style="color:{color};font-size:26px;font-weight:800;padding-top:2px;">{value}<span style="font-size:13px;">{unit}</span></div>'
        f'</td></tr></table></td>')
    store = esc((report.get("input") or {}).get("store"))
    hello = f"{esc(name)} 사장님, 의견 고맙습니다. 화면에서 보신 리포트를 보내 드려요." if name else "화면에서 보신 리포트를 보내 드려요."
    warn = (f'<div style="margin-top:12px;padding:10px 12px;border-radius:10px;background:#fff8e7;color:#8a641b;font-size:12px;">'
            f'<b>신뢰도 낮음</b> · 정상적으로 받은 AI 답변이 충분하지 않아 결과가 실제와 다를 수 있어요.</div>') if summary.get("low_reliability") else ""
    return (
        f'<tr><td style="padding:0 0 6px;color:{PURPLE};font-size:13px;font-weight:800;">{SERVICE_NAME}</td></tr>'
        f'<tr><td style="padding:0 0 14px;color:{SUB};font-size:13px;">{hello}</td></tr>'
        f'<tr><td><table {TABLE} style="background:{HERO};border-radius:24px;"><tr><td style="padding:28px 22px 22px;">'
        f'<div style="color:{MUTE};font-size:12px;font-weight:700;">{store} · AI 점검 리포트</div>'
        f'<div style="color:{INK};font-size:24px;font-weight:800;line-height:1.4;padding:10px 0 20px;letter-spacing:-0.5px;">{headline}</div>'
        f'<table {TABLE}><tr>{stat("AI 노출률", esc(rate if rate is not None else "—"), "%" + grade_html, PURPLE)}'
        f'{stat("나올 때 평균 순위", esc(avg if avg is not None else "—"), "위" if avg is not None else "")}'
        f'{stat("받은 AI 답변", valid, "개")}</tr></table>{warn}'
        f'<div style="color:{MUTE};font-size:11px;padding-top:14px;">{esc(report.get("notice") or "AI가 생성한 추정치입니다.")}</div>'
        f'</td></tr></table></td></tr>'
    )


def overview(report: dict, rows: list[dict]) -> str:
    summary = report.get("summary") or {}
    mention = summary.get("mention") or {}
    rate, valid, hit = mention.get("rate"), mention.get("valid") or 0, mention.get("mentioned") or 0
    cards = []

    # 1) 노출률: 등급 띠(약함 25 · 보통 25 · 강함 50) + 지금 위치(▲)
    g = grade_of(rate)
    word = {"강함": "잘 나오는 편이에요", "보통": "보통이에요"}.get(g[1] if g else "", "아직 약한 편이에요")
    scale = (f'<table {TABLE}><tr><td width="25%" style="background:#f6a0a8;height:10px;font-size:0;">&nbsp;</td>'
             f'<td width="25%" style="background:#fbd38a;height:10px;font-size:0;">&nbsp;</td>'
             f'<td width="50%" style="background:#80d4ad;height:10px;font-size:0;">&nbsp;</td></tr></table>')
    marker = (f'<table {TABLE}><tr><td width="{max(0, min(97, rate or 0)):.0f}%" style="font-size:0;">&nbsp;</td>'
              f'<td style="color:{INK};font-size:12px;font-weight:800;">▲ 지금 {esc(rate)}%</td></tr></table>') if rate is not None else ""
    cards.append(card("AI 노출률", f"노출률 {b(esc(rate) + '%')}, {word}" if rate is not None else "노출률을 계산하지 못했어요",
                      scale + marker + f'<div style="color:{MUTE};font-size:11px;padding-top:8px;">약함 ~25% · 보통 ~50% · 강함 50%~ (해외 GEO 측정 가이드의 참고 기준)</div>'))

    # 2) AI가 우리 가게를 소개한 말 (의견 팝업 2번 질문과 같은 이름)
    quotes = (summary.get("descriptions") or [])[:3]
    body = "".join(white_box(f'<span style="color:{INK};font-size:14px;">“{esc(d.get("text"))}”</span>'
                             f'<span style="color:{MUTE};font-size:12px;font-weight:700;"> · {esc(d.get("count"))}번</span>') for d in quotes)
    if not quotes:
        body = f'<div style="color:{SUB};font-size:13px;">{"우리 가게가 나온 답변에 소개 문장이 없었어요." if hit else "우리 가게가 나온 답변이 없어요."}</div>'
    cards.append(card("AI가 우리 가게를 소개한 말", "AI는 우리 가게를 이렇게 소개해요" if quotes else "AI 답변에서 우리 가게를 소개한 말이 없어요", body))

    # 3) AI 답변에 함께 나온 가게 · 점유율 (의견 팝업 3번 질문과 같은 이름). 메일은 도넛 대신 한 줄 나눔 막대
    parts, top = share_of(report)
    total = sum(p["value"] for p in parts)
    if not top:
        share_title = "함께 나온 다른 가게가 없어요"
    elif hit >= (top.get("answers") or 0):
        share_title = f"{b('우리 가게')}가 가장 많이 나왔어요"
    elif not hit:
        share_title = f"{b(esc(josa(top.get('name', ''), '이', '가')), RED)} 가장 많이 나왔어요"
    else:
        times = jsround((top.get("answers") or 0) / hit)
        share_title = f"{b(esc(josa(top.get('name', ''), '이', '가')), RED)} 우리보다 " + (f"{times}배 많이 나왔어요" if times >= 2 else "조금 더 많이 나왔어요")
    strip = "".join(f'<td width="{pct(p["value"], total)}%" style="background:{p["color"]};height:16px;font-size:0;">&nbsp;</td>'
                    for p in parts if pct(p["value"], total) > 0) or f'<td style="background:{WHITE};height:16px;font-size:0;">&nbsp;</td>'
    legend = "".join(
        f'<tr><td width="16" style="padding:3px 0;"><span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:{p["color"]};"></span></td>'
        f'<td style="padding:3px 0;font-size:12px;color:{PURPLE_INK if p.get("us") else SUB};font-weight:{800 if p.get("us") else 400};">{esc(p["label"])}</td>'
        f'<td align="right" style="font-size:12px;font-weight:700;color:{INK};">{pct(p["value"], total)}%</td></tr>' for p in parts)
    shops = "".join(white_box(
        f'<table {TABLE}><tr><td width="30" valign="top">{tag(i + 1, GREYS[i]).replace("color:#ffffff", "color:" + SUB)}</td>'
        f'<td><div style="color:{INK};font-size:14px;font-weight:700;">{esc(c.get("name"))}</div>'
        f'<div style="color:{SUB};font-size:12px;">{esc(c.get("description") or "소개 문장 없음")}</div></td>'
        f'<td width="70" align="right" valign="top" style="color:{MUTE};font-size:12px;">답변 {esc(c.get("answers") or 0)}개</td></tr></table>')
        for i, c in enumerate((summary.get("competitors") or [])[:3]))
    cards.append(card("AI 답변에 함께 나온 가게 · 점유율", share_title,
                      f'<table {TABLE} style="border-radius:8px;"><tr>{strip}</tr></table><table {TABLE} style="margin-top:10px;">{legend}</table>{shops}'))

    # 4) 몇 번째로 소개됐나
    ok = [a for a in report.get("answers") or [] if a.get("status") == "ok"]
    ranked = [a for a in ok if a.get("mentioned")]
    is_num = lambda r: isinstance(r, int) and not isinstance(r, bool)  # noqa: E731
    rank_rows = [
        {"label": "1위", "value": sum(1 for a in ranked if a.get("rank") == 1)},
        {"label": "2~3위", "value": sum(1 for a in ranked if a.get("rank") in (2, 3))},
        {"label": "4위 이하", "value": sum(1 for a in ranked if is_num(a.get("rank")) and a["rank"] >= 4)},
        {"label": "순위 없음", "value": sum(1 for a in ranked if not is_num(a.get("rank")))},
        {"label": "안 나옴", "value": valid - len(ranked), "color": GREYS[1]},
    ]
    rank_rows = [r for r in rank_rows if r["label"] != "순위 없음" or r["value"] > 0]
    avg = (summary.get("rank") or {}).get("average")
    rank_title = f"나올 때는 평균 {b(esc(avg) + '위')}예요" if avg is not None else ("목록이 아닌 답변에서만 나왔어요" if hit else "아직 순위에 오르지 못했어요")
    cards.append(card("몇 번째로 소개됐나", rank_title, bars(rank_rows, valid)))

    # 5) 어떤 분위기로 소개했나
    s = summary.get("sentiment") or {}
    pos, neu, neg = s.get("긍정") or 0, s.get("중립") or 0, s.get("부정") or 0
    st = pos + neu + neg
    sent_title = ("소개된 답변이 없어 분위기를 알 수 없어요" if not st else f"나쁘게 소개한 답변이 {b(str(neg) + '개', RED)} 있어요" if neg
                  else f"나온 답변은 모두 {b('좋게')} 소개했어요" if pos == st else f"좋게 소개한 답변이 {b(str(pct(pos, st)) + '%')}예요")
    cards.append(card("어떤 분위기로 소개했나", sent_title, bars([
        {"label": "긍정", "value": pos, "color": GREEN}, {"label": "중립", "value": neu, "color": GREYS[0]},
        {"label": "부정", "value": neg, "color": RED}], st)))

    # 6) AI가 참고한 출처
    kinds = sorted((summary.get("sources") or {}).get("kinds", {}).items(), key=lambda kv: -kv[1])
    src_total = (summary.get("sources") or {}).get("total") or sum(n for _, n in kinds)
    if not src_total or not kinds:
        src_title = "AI가 출처를 남기지 않았어요"
    elif kinds[0][0] == "기타":
        src_title = "여러 사이트를 고루 참고했어요"
    else:
        src_title = f"{b(esc(josa(kinds[0][0], '을', '를')))} 가장 많이 봤어요 ({pct(kinds[0][1], src_total)}%)"
    cards.append(card("AI가 참고한 출처", src_title, bars([{"label": k, "value": n} for k, n in kinds[:5]], kinds[0][1] if kinds else 1)))

    # 7) 질문 유형별
    types = list((summary.get("by_type") or {}).items())
    measured = [(t, v) for t, v in types if v.get("valid")]
    rates = [v.get("rate") or 0 for _, v in measured]
    if not measured:
        type_title = "유형별로 셀 답변이 없어요"
    elif max(rates) == 0:
        type_title = "모든 유형에서 아직 나오지 않아요"
    elif min(rates) == max(rates):
        type_title = "유형별로 고르게 나왔어요"
    else:
        weakest = next(t for t, v in measured if (v.get("rate") or 0) == min(rates))
        type_title = f"{b(esc(weakest), RED)} 질문에서 가장 약해요"
    type_rows = [{"label": t, "value": v.get("mentioned") or 0, "text": f"{v.get('mentioned') or 0}/{v['valid']}" if v.get("valid") else "—",
                  "low": bool(v.get("valid")) and not v.get("mentioned")} for t, v in types]
    cards.append(card("질문 유형별", type_title, bars(type_rows, max([1] + [v.get("valid") or 0 for _, v in measured]))))

    # 8) 질문 × 답변 지도
    hit_q = sum(1 for r in rows if r["hit"] > 0)
    heat_title = ("아직 어떤 질문에서도 나오지 않았어요" if not hit_q else "모든 질문에서 한 번 이상 나왔어요" if hit_q == len(rows)
                  else f"질문 {len(rows)}개 중 {b(str(hit_q) + '개')}에서만 우리 가게가 나왔어요")
    cell = {"hit": PURPLE, "miss": WHITE, "fail": "#dfe2e7"}
    heat = "".join(
        f'<tr><td style="padding:3px 0;color:{SUB};font-size:12px;">{esc(r["text"])}</td>'
        + "".join(f'<td width="26" style="padding:3px 2px;"><div style="height:16px;border-radius:5px;background:{cell[st]};font-size:0;">&nbsp;</div></td>' for st in r["states"])
        + "</tr>" for r in rows)
    cards.append(card(f"질문 {len(rows)}개 × 답변 3번", heat_title,
                      f'<table {TABLE}>{heat}</table><div style="color:{MUTE};font-size:11px;padding-top:8px;">보라 칸 = 우리 가게가 나온 답변 · 회색 칸 = AI가 답하지 못한 경우</div>'))

    return section_head("한눈에 보기", f"AI 답변 {valid}개를 여덟 가지로 나눠 봤어요.") + "".join(cards)


def questions(rows: list[dict]) -> str:
    out = ""
    for r in rows:
        badge_bg, badge_fg = (PURPLE_SOFT, PURPLE_INK) if r["hit"] else (CARD, MUTE)
        out += (f'<tr><td style="padding:12px 0;border-top:1px solid #e5e8eb;">'
                f'<div style="color:{MUTE};font-size:11px;font-weight:700;">{esc(r["type"])}</div>'
                f'<div style="color:{INK};font-size:14px;font-weight:700;">{esc(r["text"])}</div></td>'
                f'<td width="104" align="right" style="padding:12px 0;border-top:1px solid #e5e8eb;">'
                f'<span style="display:inline-block;padding:3px 9px;border-radius:20px;background:{badge_bg};color:{badge_fg};font-size:11px;font-weight:800;">'
                f'{r["valid"]}번 중 {r["hit"]}번 나옴</span></td></tr>')
    return (section_head("AI에게 물어본 질문", "AI 답변 원문은 메일에 넣지 않았어요. 질문마다 우리 가게가 나온 횟수만 보여 드려요.")
            + f'<tr><td><table {TABLE} style="border-bottom:1px solid #e5e8eb;">{out}</table></td></tr>')


def agent_section(report: dict) -> str:
    agent = report.get("agent") or {}
    if not agent.get("ran"):
        return ""                                            # 메일에서는 [더 자세히 진단하기]를 누를 수 없으니 칸을 넣지 않음
    sub = ("[더 자세히 진단하기]로 AI가 스스로 질문을 골라 더 물어봤어요." if agent.get("trigger") == "button"
           else "노출률이 낮아서 AI가 스스로 질문을 골라 더 물어봤어요.")
    out = ""
    for t in agent.get("trace") or []:
        what, yes, no = TOOLS.get(t.get("tool_label"), ("", "추가 질문에서 우리 가게가 나왔어요", "추가 질문에서도 우리 가게가 나오지 않았어요"))
        valid, hit = (t.get("result") or {}).get("valid") or 0, (t.get("result") or {}).get("mentioned") or 0
        title = "추가 질문의 답변을 받지 못했어요" if not valid else yes if hit else no
        dots = "".join(f'<span style="color:{PURPLE if i < hit else "#c9ced6"};font-size:14px;">●</span>' for i in range(valid))
        body = (f'<div style="color:{SUB};font-size:13px;">추가 질문 답변 {valid}번 중 <b style="color:{INK};">{hit}번</b> 나왔어요 {dots}</div>'
                + (f'<div style="color:{MUTE};font-size:12px;padding-top:6px;">{what}</div>' if what else "")
                + (white_box(f'<div style="color:{MUTE};font-size:11px;font-weight:700;">AI가 고른 질문</div><div style="color:{INK};font-size:14px;">“{esc(t.get("question"))}”</div>') if t.get("question") else "")
                + white_box(f'<div style="color:{MUTE};font-size:11px;font-weight:700;">이 질문을 고른 이유</div><div style="color:{INK};font-size:14px;">{esc(t.get("why") or "별도 설명 없음")}</div>'))
        out += card(esc(t.get("tool_label") or "추가 질문"), b(title, INK if hit else "#d43846"), body)
    reason = (f'<tr><td style="padding:0 0 10px;"><span style="display:inline-block;padding:5px 11px;border-radius:14px;background:{CARD};color:{SUB};font-size:12px;font-weight:700;">'
              f'실행 이유 · {esc(agent.get("reason_to_run"))}</span></td></tr>') if agent.get("reason_to_run") else ""
    return section_head("AI 추가 진단", sub) + reason + out


def suggestions_section(report: dict) -> str:
    items = []
    spots = weak_spots(report)
    for i, s in enumerate((report.get("suggestions") or [])[:3]):
        link = link_of(s, spots)
        spot = spots[link] if link >= 0 else None
        items.append({**s, "no": i + 1, "color": TAG_COLORS[i], "link": link, "spot": spot, "nums": numbers_of(s.get("evidence"), spot)})
    head = section_head("개선 제안", "진단에서 약했던 곳을 바탕으로 해 볼 일을 골랐어요.")
    if not items:
        return head + f'<tr><td style="color:{SUB};font-size:13px;">개선 제안을 만들지 못했어요.</td></tr>'

    linked = sorted((it for it in items if it["link"] >= 0), key=lambda it: (it["link"], it["no"]))
    first = linked[0] if linked else items[0]
    rest = [it for it in items if it["no"] != first["no"]]

    # 가장 먼저 해 볼 일 (보라 카드)
    nums = (f'<td width="96" align="center" valign="middle"><div style="color:#ffffff;font-size:26px;font-weight:800;">{first["nums"][0]}/{first["nums"][1]}</div>'
            f'<div style="color:#ffffff;font-size:11px;opacity:0.85;">지금</div></td>') if first["nums"] else ""
    sp = first["spot"]
    reason = (f'{esc(josa(sp["label"], "이", "가"))} 약해서 먼저 골랐어요 ({esc(sp.get("text") or str(sp["hit"]) + "/" + str(sp["of"]))}).'
              if sp else "AI가 첫 번째로 낸 제안이에요.")
    spot_html = (
        f'<tr><td style="padding:0 0 12px;"><table {TABLE} style="background:{PURPLE};border-radius:20px;"><tr><td style="padding:24px;">'
        f'<table {TABLE}><tr><td valign="top">'
        f'<div style="color:#ffffff;font-size:12px;font-weight:700;opacity:0.9;">{tag(first["no"], "#8a7de6")} 가장 먼저 해 볼 일</div>'
        f'<div style="color:#ffffff;font-size:20px;font-weight:800;line-height:1.4;padding-top:8px;">{esc(first.get("title"))}</div>'
        f'<div style="color:#ffffff;font-size:13px;line-height:1.7;padding-top:6px;opacity:0.92;">{esc(first.get("detail"))}</div>'
        + (f'<div style="padding-top:10px;"><span style="display:inline-block;padding:5px 11px;border-radius:14px;background:#8a7de6;color:#ffffff;font-size:12px;font-weight:700;">왜? {esc(first.get("evidence"))}</span></div>' if first.get("evidence") else "")
        + f'<div style="color:#ffffff;font-size:12px;padding-top:8px;opacity:0.8;">{reason}</div>'
        f'</td>{nums}</tr></table></td></tr></table></td></tr>')

    # 약한 곳 → 할 일 연결 (같은 번호·색)
    linked_ids = {it["link"] for it in items}
    weak_rows = ""
    for i, spot in enumerate(spots):
        if i >= 4 and i not in linked_ids:
            continue
        owner = next((it for it in items if it["link"] == i), None)
        mark = tag(owner["no"], owner["color"]) if owner else tag("–", GREYS[1]).replace("color:#ffffff", "color:" + SUB)
        weak_rows += (f'<tr><td width="30" style="padding:6px 0 0;">{mark}</td><td style="padding:6px 0 0;color:{INK};font-size:13px;">{esc(spot["label"])}</td>'
                      f'<td align="right" style="padding:6px 0 0;color:{RED};font-size:13px;font-weight:800;">{esc(spot.get("text") or str(spot["hit"]) + "/" + str(spot["of"]))}</td></tr>'
                      f'<tr><td></td><td colspan="2" style="padding:4px 0 2px;">{bar_cell(max(3, spot["hit"] / spot["of"] * 100), RED, WHITE, 6)}</td></tr>')
    missed = next((s for i, s in enumerate(spots) if s["hit"] == 0 and i not in linked_ids), None)
    missed_html = (f'<div style="margin-top:10px;padding:8px 10px;border-radius:10px;background:{WARN_SOFT};color:#9a6a12;font-size:12px;">'
                   f'{esc(missed["label"])}({missed["hit"]}/{missed["of"]})에 대한 제안은 아직 없어요.</div>') if missed else ""
    weak_html = card("AI 답변에서 약한 곳", "약한 곳과 제안을 같은 번호로 이었어요", f'<table {TABLE}>{weak_rows}</table>{missed_html}')

    # 그다음 할 일
    todo = ""
    for it in rest:
        todo += card(f'{tag(it["no"], it["color"])} &nbsp;{esc("약한 곳: " + it["spot"]["label"]) if it["spot"] else "근거를 바탕으로 한 제안"}',
                     esc(it.get("title")),
                     f'<div style="color:{SUB};font-size:13px;line-height:1.7;">{esc(it.get("detail"))}</div>'
                     + (f'<div style="padding-top:8px;"><span style="display:inline-block;padding:4px 10px;border-radius:8px;background:{RED_SOFT};color:{RED};font-size:12px;font-weight:700;">근거: {esc(it.get("evidence"))}</span></div>' if it.get("evidence") else ""))
    return head + spot_html + weak_html + todo


def build_report_html(report: dict, name: str = "") -> str:
    """리포트(dict) → 메일 본문 HTML 한 덩어리. 화면 리포트와 같은 순서로 만든다."""
    rows = question_rows(report)
    parts = [hero(report, name), overview(report, rows), questions(rows), agent_section(report), suggestions_section(report)]
    footer = (f'<tr><td style="padding:30px 0 6px;color:{SUB};font-size:12px;line-height:1.8;">'
              f'답변 원문과 [더 자세히 진단하기]는 화면에서 볼 수 있어요. 언제든 다시 점검할 수 있어요: '
              f'<a href="{SITE_URL}" style="color:{PURPLE};">{SITE_URL}</a></td></tr>'
              f'<tr><td style="padding:6px 0;color:{MUTE};font-size:11px;">{SERVICE_NAME} · AI가 생성한 추정치 · 실제 AI 앱 답변과 다를 수 있음</td></tr>')
    return (f'<div style="margin:0;padding:24px 12px;background:{PAGE};font-family:{FONT};">'
            f'<table {TABLE} style="max-width:640px;margin:0 auto;">{"".join(parts)}{footer}</table></div>')
