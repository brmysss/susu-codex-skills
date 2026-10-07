#!/usr/bin/env python3
"""Render a fact/opinion analysisData JSON object as a self-contained HTML report.

The renderer intentionally uses only Python's standard library. It does not fetch
remote resources and escapes all user-provided text before putting it in HTML.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


POS_LABELS = {
    "noun": "名词",
    "verb": "动词",
    "adjective": "形容词",
    "adverb": "副词",
    "other": "其他标记",
}


def text(value: Any, default: str = "") -> str:
    """Return a human-readable string without leaking Python's None."""

    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def escape(value: Any, default: str = "") -> str:
    return html.escape(text(value, default), quote=True)


def first(item: dict[str, Any], *names: str, default: str = "") -> str:
    for name in names:
        value = item.get(name)
        if value not in (None, "", []):
            return text(value)
    return default


def safe_json(value: Any) -> str:
    """Embed JSON safely in a script block."""

    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def render_table(
    title: str,
    items: list[dict[str, Any]],
    columns: list[tuple[str, tuple[str, ...]]],
    section_id: str,
) -> str:
    if not items:
        return (
            f'<section class="report-section" id="{escape(section_id)}">'
            f'<h3>{escape(title)}</h3><p class="empty">暂无记录。</p></section>'
        )

    head = "".join(f"<th scope=\"col\">{escape(label)}</th>" for label, _ in columns)
    rows: list[str] = []
    for item in items:
        cells = []
        for _, names in columns:
            value = first(item, *names, default="—")
            cells.append(f"<td>{escape(value)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")

    return (
        f'<section class="report-section" id="{escape(section_id)}">'
        f"<h3>{escape(title)} <span class=\"count\">{len(items)}</span></h3>"
        '<div class="table-wrap"><table><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div></section>"
    )


def token_class(pos: str) -> str:
    return pos if pos in POS_LABELS else "other"


def render_segment(segment: dict[str, Any], token_map: dict[str, dict[str, Any]]) -> str:
    visible = text(segment.get("text"))
    token_id = text(segment.get("tokenId"))
    token = token_map.get(token_id)
    if not token_id or token is None:
        return escape(visible)

    pos = token_class(text(token.get("pos"), "other"))
    label = f"查看词语：{text(token.get('word'), visible)}，词性：{POS_LABELS[pos]}"
    return (
        f'<button type="button" class="token token-{escape(pos)}" '
        f'data-token-id="{escape(token_id)}" aria-label="{escape(label)}">'
        f"{escape(visible)}</button>"
    )


def render_paragraphs(source: dict[str, Any], token_map: dict[str, dict[str, Any]]) -> str:
    paragraphs = source.get("paragraphs") or []
    if not isinstance(paragraphs, list):
        paragraphs = []

    rendered: list[str] = []
    for index, paragraph in enumerate(paragraphs, start=1):
        if not isinstance(paragraph, dict):
            continue
        paragraph_id = first(paragraph, "id", default=f"P{index:02d}")
        segments = paragraph.get("segments")
        if isinstance(segments, list):
            body = "".join(
                render_segment(segment, token_map)
                for segment in segments
                if isinstance(segment, dict)
            )
        else:
            body = escape(paragraph.get("text"), "")
        rendered.append(
            '<article class="source-paragraph">'
            f'<span class="paragraph-id">{escape(paragraph_id)}</span>'
            f'<p>{body or "<span class=\"empty\">（空段落）</span>"}</p>'
            "</article>"
        )

    if rendered:
        return "".join(rendered)

    plain_text = first(source, "text", default="")
    if plain_text:
        return (
            '<article class="source-paragraph"><span class="paragraph-id">原文</span>'
            f"<p>{escape(plain_text)}</p></article>"
        )
    return '<p class="empty">未提供可展示的原文段落。</p>'


def build_pos_summary(tokens: list[dict[str, Any]]) -> list[dict[str, str]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "words": Counter(), "roles": set(), "lenses": set(), "sources": set()}
    )
    for token in tokens:
        pos = token_class(text(token.get("pos"), "other"))
        group = grouped[pos]
        group["count"] += 1
        word = first(token, "word", default="—")
        group["words"][word] += 1
        role = first(token, "role")
        lens = first(token, "lens")
        source = first(token, "source")
        if role:
            group["roles"].add(role)
        if lens:
            group["lenses"].add(lens)
        if source:
            group["sources"].add(source)

    summary: list[dict[str, str]] = []
    for pos in ("noun", "verb", "adjective", "adverb", "other"):
        group = grouped.get(pos)
        if not group:
            continue
        words = "、".join(
            f"{word}（{count}）" for word, count in group["words"].most_common()
        )
        summary.append(
            {
                "词类": POS_LABELS[pos],
                "词语": words,
                "频次": str(group["count"]),
                "语义角色": "、".join(sorted(group["roles"])) or "—",
                "论断视角": "、".join(sorted(group["lenses"])) or "—",
                "出处": "、".join(sorted(group["sources"])) or "—",
            }
        )
    return summary


def render_pos_summary(summary: list[dict[str, str]]) -> str:
    if not summary:
        return (
            '<section class="report-section" id="pos-summary">'
            "<h3>词性汇总</h3><p class=\"empty\">未提供词语标注。</p></section>"
        )

    headers = ["词类", "词语", "频次", "语义角色", "论断视角", "出处"]
    head = "".join(f'<th scope="col">{escape(header)}</th>' for header in headers)
    rows = []
    for row in summary:
        rows.append(
            "<tr>"
            + "".join(f"<td>{escape(row.get(header, '—'))}</td>" for header in headers)
            + "</tr>"
        )
    return (
        '<section class="report-section" id="pos-summary">'
        "<h3>词性汇总</h3><div class=\"table-wrap\"><table><thead><tr>"
        + head
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div></section>"
    )


def render_token_table(tokens: list[dict[str, Any]]) -> str:
    columns = [
        ("词语", ("word",)),
        ("词性", ("pos",)),
        ("语义角色", ("role",)),
        ("论断视角", ("lens",)),
        ("出处", ("source",)),
    ]
    items = []
    for token in tokens:
        item = dict(token)
        item["pos"] = POS_LABELS.get(token_class(text(token.get("pos"))), "其他标记")
        items.append(item)
    return render_table("词语标注明细", items, columns, "token-details")


def render_structure(structure: Any) -> str:
    if not isinstance(structure, list) or not structure:
        return ""
    pills = "".join(f'<span class="pill">{escape(item)}</span>' for item in structure)
    return f'<div class="structure"><span class="eyebrow">结构</span>{pills}</div>'


def render_boundaries(data: dict[str, Any]) -> str:
    notes = data.get("pendingVerification") or data.get("boundaries") or []
    if not isinstance(notes, list):
        notes = [notes]
    items = "".join(f"<li>{escape(note)}</li>" for note in notes if note)
    if not items:
        items = (
            "<li>“原文称述”不等于“外部已核实”；本页面不会自动把作者的事实性断言当成世界事实。</li>"
            "<li>词性标注与事实／观点分类是两个维度，不能互相替代。</li>"
        )
    return (
        '<section class="boundary" id="boundaries">'
        "<h3>边界与待核验项</h3>"
        f"<ul>{items}</ul></section>"
    )


def render_html(data: dict[str, Any]) -> str:
    source = data.get("source") or {}
    summary = data.get("summary") or {}
    if not isinstance(source, dict):
        source = {}
    if not isinstance(summary, dict):
        summary = {}

    app_version = first(data, "appVersion", default="0.4.0")
    title = first(source, "title", default="事实和观点判断报告")
    source_type = first(source, "type", default="未注明来源类型")
    source_scope = first(source, "scope", default="全文")
    source_url = first(source, "url")
    tokens = data.get("tokens") or []
    if not isinstance(tokens, list):
        tokens = []
    tokens = [token for token in tokens if isinstance(token, dict)]
    token_map = {first(token, "id"): token for token in tokens if first(token, "id")}
    paragraphs = source.get("paragraphs") if isinstance(source.get("paragraphs"), list) else []

    factual_claims = data.get("factualClaims") or []
    opinions = data.get("opinions") or []
    actions = data.get("actions") or []
    argument_chain = data.get("argumentChain") or []
    factual_claims = [item for item in factual_claims if isinstance(item, dict)]
    opinions = [item for item in opinions if isinstance(item, dict)]
    actions = [item for item in actions if isinstance(item, dict)]
    argument_chain = [item for item in argument_chain if isinstance(item, dict)]

    source_link = ""
    if source_url:
        source_link = (
            f'<a class="source-link" href="{escape(source_url)}" '
            'target="_blank" rel="noopener noreferrer">打开来源 ↗</a>'
        )

    footer_link = data.get("footerLink") or {}
    footer = ""
    if isinstance(footer_link, dict) and first(footer_link, "url"):
        footer = (
            '<a href="'
            + escape(first(footer_link, "url"))
            + '" target="_blank" rel="noopener noreferrer">'
            + escape(first(footer_link, "label", default="打开主页"))
            + " ↗</a>"
        )

    token_details = {
        first(token, "id"): {
            "word": first(token, "word"),
            "pos": POS_LABELS.get(token_class(first(token, "pos")), "其他标记"),
            "role": first(token, "role", default="未提供"),
            "lens": first(token, "lens", default="未提供"),
            "note": first(token, "note", default="未提供"),
            "sentence": first(token, "sentence", default="未提供"),
            "source": first(token, "source", default="未提供"),
        }
        for token in tokens
        if first(token, "id")
    }

    stats = [
        ("原文段落", len(paragraphs)),
        ("事实性断言", len(factual_claims)),
        ("观点／立场", len(opinions)),
        ("词语标注", len(tokens)),
    ]
    stat_cards = "".join(
        f'<div class="stat"><strong>{count}</strong><span>{escape(label)}</span></div>'
        for label, count in stats
    )

    factual_table = render_table(
        "事实性断言",
        factual_claims,
        [
            ("ID", ("id",)),
            ("来源", ("source",)),
            ("断言", ("claim",)),
            ("归属", ("attribution",)),
            ("状态", ("status",)),
            ("依据／缺口", ("evidence", "gap")),
        ],
        "factual-claims",
    )
    opinion_table = render_table(
        "观点、解释与立场",
        opinions,
        [
            ("ID", ("id",)),
            ("来源", ("source",)),
            ("观点", ("claim",)),
            ("类型", ("type",)),
            ("论据／理由", ("reason", "evidence", "support")),
            ("隐含假设", ("assumption",)),
            ("支持度", ("support",)),
            ("缺口", ("gap",)),
        ],
        "opinions",
    )
    action_table = render_table(
        "行动建议与规范性结论",
        actions,
        [
            ("ID", ("id",)),
            ("来源", ("source",)),
            ("建议", ("action",)),
            ("目标对象", ("target", "audience")),
            ("依据", ("basis", "reason")),
            ("风险／边界", ("boundary", "risk")),
        ],
        "actions",
    )
    argument_table = render_table(
        "论题—论据—论证—结论",
        argument_chain,
        [
            ("步骤／论题", ("step", "topic")),
            ("内容／论据", ("content", "evidence")),
            ("来源", ("source",)),
            ("结论／备注", ("conclusion", "note")),
        ],
        "argument-chain",
    )

    raw_json = escape(json.dumps(data, ensure_ascii=False, indent=2))
    thesis = first(summary, "thesis", default="未提供一句话主旨")
    structure = render_structure(summary.get("structure"))
    json_token_data = safe_json(token_details)

    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} · 事实和观点判断</title>
  <style>
    :root {{
      --ink: #17221f; --muted: #64706c; --paper: #f7f4ec; --card: #fffdf8;
      --line: #ddd8ca; --accent: #d65d49; --teal: #258c83; --gold: #bf851e;
      --purple: #8068b6; --shadow: 0 18px 55px rgba(28, 42, 36, .10);
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; color: var(--ink); background: var(--paper); font: 15px/1.75 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; }}
    a {{ color: inherit; }}
    .shell {{ width: min(1440px, calc(100% - 32px)); margin: 0 auto; padding: 28px 0 54px; }}
    .hero {{ display: flex; justify-content: space-between; gap: 24px; align-items: flex-start; padding: 24px 28px; color: #f8f5eb; background: #172b28; border-radius: 22px; box-shadow: var(--shadow); }}
    .eyebrow {{ color: #d9ad51; font-size: 12px; letter-spacing: .14em; text-transform: uppercase; font-weight: 700; }}
    h1, h2, h3, p {{ margin-top: 0; }}
    h1 {{ margin-bottom: 7px; font-family: Georgia, "Songti SC", serif; font-size: clamp(26px, 4vw, 46px); line-height: 1.2; }}
    .meta {{ margin: 0; color: #cbd6ce; }}
    .version {{ flex: 0 0 auto; color: #172b28; background: #e5bd64; border-radius: 999px; padding: 5px 11px; font-size: 12px; font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.08fr); gap: 22px; margin-top: 22px; align-items: start; }}
    .panel, .report-section, .boundary, .overview {{ background: var(--card); border: 1px solid var(--line); border-radius: 18px; box-shadow: 0 8px 24px rgba(28, 42, 36, .04); }}
    .panel {{ padding: 22px; min-width: 0; }}
    .panel > h2 {{ margin-bottom: 5px; font-size: 20px; }}
    .source-meta {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px 14px; color: var(--muted); font-size: 13px; margin-bottom: 18px; }}
    .source-link {{ color: var(--teal); font-weight: 700; text-decoration: none; }}
    .source-paragraph {{ position: relative; display: block; padding: 16px 0 16px 58px; border-top: 1px dashed var(--line); }}
    .source-paragraph:first-child {{ border-top: 0; padding-top: 5px; }}
    .source-paragraph p {{ margin: 0; font-family: Georgia, "Songti SC", serif; font-size: clamp(17px, 1.8vw, 21px); line-height: 2.05; white-space: pre-wrap; overflow-wrap: anywhere; }}
    .paragraph-id {{ position: absolute; left: 0; top: 18px; color: var(--accent); font: 700 12px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace; }}
    .source-paragraph:first-child .paragraph-id {{ top: 7px; }}
    .token {{ cursor: pointer; padding: 0 2px; border: 0; border-bottom: 3px solid; background: transparent; color: inherit; font: inherit; line-height: inherit; transition: opacity .16s, background .16s; }}
    .token:hover, .token:focus-visible {{ outline: 2px solid currentColor; outline-offset: 2px; background: rgba(255,255,255,.75); }}
    .token-noun {{ border-color: var(--accent); }} .token-verb {{ border-color: var(--teal); }} .token-adjective {{ border-color: var(--gold); }} .token-adverb {{ border-color: var(--purple); }} .token-other {{ border-color: #86918c; }}
    .token[data-dimmed="true"] {{ opacity: .18; }}
    .legend, .filters {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 12px 0 18px; }}
    .legend-item, .filter {{ border: 1px solid var(--line); border-radius: 999px; padding: 3px 10px; background: #fbfaf4; font-size: 12px; }}
    .legend-item::before {{ content: ""; display: inline-block; width: 8px; height: 8px; margin-right: 5px; border-radius: 50%; background: currentColor; }}
    .legend-noun {{ color: var(--accent); }} .legend-verb {{ color: var(--teal); }} .legend-adjective {{ color: var(--gold); }} .legend-adverb {{ color: var(--purple); }}
    .filter {{ cursor: pointer; color: var(--ink); }} .filter[aria-pressed="true"] {{ color: #fff; background: var(--ink); border-color: var(--ink); }}
    .overview {{ padding: 18px; margin-bottom: 22px; }}
    .overview h2 {{ margin-bottom: 8px; font-size: 18px; }}
    .thesis {{ margin-bottom: 12px; font-size: 18px; }}
    .structure {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
    .pill {{ display: inline-block; padding: 4px 10px; border-radius: 999px; background: #edf3ee; color: #246459; font-size: 12px; }}
    .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 17px; }}
    .stat {{ padding: 11px 12px; border-radius: 12px; background: #f1eee5; }} .stat strong {{ display: block; font-size: 23px; line-height: 1.15; }} .stat span {{ color: var(--muted); font-size: 12px; }}
    .report-section {{ padding: 18px; margin-bottom: 14px; }}
    .report-section h3, .boundary h3 {{ display: flex; justify-content: space-between; gap: 12px; margin-bottom: 12px; font-size: 17px; }}
    .count {{ color: var(--muted); font-size: 12px; font-weight: 500; }}
    .table-wrap {{ overflow-x: auto; }} table {{ width: 100%; min-width: 580px; border-collapse: collapse; font-size: 13px; }} th, td {{ padding: 9px 10px; border-top: 1px solid var(--line); text-align: left; vertical-align: top; }} th {{ color: var(--muted); font-size: 12px; white-space: nowrap; }}
    .boundary {{ padding: 18px; background: #fff8e7; border-color: #ead7a8; }} .boundary ul {{ margin: 0; padding-left: 20px; }}
    .empty {{ color: var(--muted); font-style: italic; }}
    .token-popover {{ position: fixed; z-index: 20; top: 20px; right: 20px; width: min(380px, calc(100vw - 40px)); padding: 17px; background: #172b28; color: #f7f4ec; border-radius: 15px; box-shadow: 0 18px 50px rgba(0,0,0,.25); }}
    .token-popover[hidden] {{ display: none; }} .popover-top {{ display:flex; justify-content: space-between; gap: 12px; align-items: start; }} .popover-word {{ font-size: 23px; font-weight: 700; }} .popover-close {{ border: 0; background: transparent; color: inherit; cursor: pointer; font-size: 20px; }} .popover-grid {{ display:grid; grid-template-columns: 80px 1fr; gap: 5px 10px; margin-top: 11px; font-size: 13px; }} .popover-grid dt {{ color: #a9c0b5; }} .popover-grid dd {{ margin: 0; overflow-wrap: anywhere; }}
    footer {{ display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-top: 28px; padding: 17px 4px 0; color: var(--muted); font-size: 13px; }} footer a {{ color: var(--teal); font-weight: 700; text-decoration: none; }}
    details {{ margin-top: 14px; color: var(--muted); font-size: 12px; }} pre {{ max-height: 280px; overflow: auto; padding: 12px; border-radius: 10px; background: #f1eee5; white-space: pre-wrap; overflow-wrap: anywhere; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} .token-popover {{ top: auto; right: 16px; bottom: 16px; left: 16px; width: auto; }} }}
    @media (max-width: 560px) {{ .shell {{ width: min(100% - 20px, 1440px); padding-top: 10px; }} .hero {{ padding: 19px; border-radius: 16px; }} .panel {{ padding: 16px; }} .source-paragraph {{ padding-left: 44px; }} .stats {{ grid-template-columns: repeat(2, 1fr); }} }}
  </style>
</head>
<body>
  <main class="shell">
    <header class="hero">
      <div><div class="eyebrow">Reading Lab · 事实与观点判断</div><h1>{escape(title)}</h1><p class="meta">{escape(source_type)} · {escape(source_scope)} {source_link}</p></div>
      <div class="version">页面 v{escape(app_version)}</div>
    </header>

    <div class="grid">
      <section class="panel" aria-labelledby="reader-title">
        <h2 id="reader-title">原文标注</h2>
        <div class="legend" aria-label="词性图例">
          <span class="legend-item legend-noun">名词</span><span class="legend-item legend-verb">动词</span><span class="legend-item legend-adjective">形容词</span><span class="legend-item legend-adverb">副词</span>
        </div>
        <div class="filters" aria-label="词性筛选">
          <span class="eyebrow" style="color:var(--muted);letter-spacing:.04em">强调</span>
          <button class="filter" type="button" data-filter="all" aria-pressed="true">全部</button>
          <button class="filter" type="button" data-filter="noun" aria-pressed="false">名词</button>
          <button class="filter" type="button" data-filter="verb" aria-pressed="false">动词</button>
          <button class="filter" type="button" data-filter="adjective" aria-pressed="false">形容词</button>
          <button class="filter" type="button" data-filter="adverb" aria-pressed="false">副词</button>
        </div>
        <div id="reader">{render_paragraphs(source, token_map)}</div>
        <p class="meta" style="margin-top:16px">点击带下划线的词语查看词性、语义角色、论断视角、标注理由和原句。</p>
      </section>

      <section class="analysis" aria-labelledby="analysis-title">
        <div class="overview">
          <h2 id="analysis-title">分析结果</h2>
          <p class="thesis">{escape(thesis)}</p>
          {structure}
          <div class="stats">{stat_cards}</div>
        </div>
        {factual_table}
        {opinion_table}
        {action_table}
        {argument_table}
        {render_pos_summary(build_pos_summary(tokens))}
        {render_token_table(tokens)}
        {render_boundaries(data)}
        <details><summary>查看本页使用的数据接口</summary><pre>{raw_json}</pre></details>
      </section>
    </div>

    <aside id="token-popover" class="token-popover" hidden aria-live="polite">
      <div class="popover-top"><div><div class="eyebrow">词语详情</div><div id="popover-word" class="popover-word">—</div></div><button id="popover-close" class="popover-close" type="button" aria-label="关闭词语详情">×</button></div>
      <dl class="popover-grid"><dt>词性</dt><dd id="popover-pos">—</dd><dt>语义角色</dt><dd id="popover-role">—</dd><dt>论断视角</dt><dd id="popover-lens">—</dd><dt>标注理由</dt><dd id="popover-note">—</dd><dt>所在原句</dt><dd id="popover-sentence">—</dd><dt>来源位置</dt><dd id="popover-source">—</dd></dl>
    </aside>
  </main>
  <footer><span>事实和观点判断 · 原文称述不等于外部已核实</span>{footer}</footer>
  <script>
    const TOKEN_DETAILS = {json_token_data};
    const popover = document.getElementById('token-popover');
    const setText = (id, value) => {{ document.getElementById(id).textContent = value || '—'; }};
    const closePopover = () => {{ popover.hidden = true; }};
    document.querySelectorAll('.token').forEach((button) => {{
      button.addEventListener('click', () => {{
        const detail = TOKEN_DETAILS[button.dataset.tokenId];
        if (!detail) return;
        setText('popover-word', detail.word); setText('popover-pos', detail.pos);
        setText('popover-role', detail.role); setText('popover-lens', detail.lens);
        setText('popover-note', detail.note); setText('popover-sentence', detail.sentence);
        setText('popover-source', detail.source); popover.hidden = false;
      }});
    }});
    document.getElementById('popover-close').addEventListener('click', closePopover);
    document.addEventListener('keydown', (event) => {{ if (event.key === 'Escape') closePopover(); }});
    document.querySelectorAll('[data-filter]').forEach((filterButton) => {{
      filterButton.addEventListener('click', () => {{
        const filter = filterButton.dataset.filter;
        document.querySelectorAll('[data-filter]').forEach((button) => {{ button.setAttribute('aria-pressed', String(button === filterButton)); }});
        document.querySelectorAll('.token').forEach((token) => {{ token.dataset.dimmed = String(filter !== 'all' && !token.classList.contains('token-' + filter)); }});
      }});
    }});
  </script>
</body>
</html>
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="analysisData JSON path, or - for stdin")
    parser.add_argument("--output", "-o", required=True, help="output HTML path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.input == "-":
            raw = json.load(sys.stdin)
        else:
            with Path(args.input).open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
        if not isinstance(raw, dict):
            raise ValueError("analysisData 的顶层必须是 JSON 对象")
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_html(raw), encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"render_html_report.py: {error}", file=sys.stderr)
        return 1

    print(f"已生成 HTML：{output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
