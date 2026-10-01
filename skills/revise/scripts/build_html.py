"""review.json + paragraphs.json → 수정 전/후 비교 HTML (단일 파일, 외부 의존 없음).

원문은 review.json 에 다시 적지 않는다. 문단 id 로 paragraphs.json 에서 가져오므로 원문을 옮겨
적다 생기는 오탈자가 비교표에 끼어들지 않는다. review 쪽에 before 가 있으면(신설 문단 등) 그것을 쓴다.

실행:
    uv run --frozen --quiet --no-project python ${CLAUDE_SKILL_DIR}/scripts/build_html.py <review.json> <extract_dir> <out.html>
"""
import difflib
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

E = html.escape


def word_diff(a: str, b: str) -> tuple[str, str]:
    """어절 단위 diff. 한국어는 글자 단위로 하면 조사 하나 바뀐 것도 조각나서 읽기 어렵다."""
    ta, tb = re.findall(r"\S+|\s+", a), re.findall(r"\S+|\s+", b)
    sm = difflib.SequenceMatcher(a=ta, b=tb, autojunk=False)
    left, right = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        sa, sb = "".join(ta[i1:i2]), "".join(tb[j1:j2])
        if op == "equal":
            left.append(E(sa)); right.append(E(sb))
        else:
            if sa.strip():
                left.append(f"<del>{E(sa)}</del>")
            else:
                left.append(E(sa))
            if sb.strip():
                right.append(f"<ins>{E(sb)}</ins>")
            else:
                right.append(E(sb))
    return "".join(left), "".join(right)


def paras_html(s: str) -> str:
    return "".join(f"<p>{x}</p>" for x in s.split("\n") if x.strip()) or "<p class=muted>—</p>"


def badge(text: str, kind: str) -> str:
    return f'<span class="badge {kind}">{E(text)}</span>'


def status_kind(s: str) -> str:
    if s.startswith("유지"):
        return "keep"
    if s.startswith(("삭제", "병합")):
        return "del"
    if "사실" in s or "확인" in s:
        return "warn"
    if s.startswith(("신설", "재작성", "분할", "이동")):
        return "move"
    return "edit"


def render_para(q: dict, src: dict) -> str:
    before = q.get("before", src.get(q["id"], {}).get("text", ""))
    after = q.get("after", "")
    types = sorted({e["t"] for e in q.get("edits", [])})
    if after:
        l, r = word_diff(before, after)
        l, r = paras_html(l), paras_html(r)
    else:
        l, r = paras_html(E(before)), '<p class="muted">(삭제 또는 다른 문단에 병합 — 아래 근거 참고)</p>'
    edits = "".join(
        f"<tr><td>{badge(e['t'], 'type')}</td><td class=b>{E(e['b'])}</td>"
        f"<td class=a>{E(e['a'])}</td><td>{E(e['why'])}</td></tr>" for e in q.get("edits", []))
    checks = "".join(f"<li>{E(c)}</li>" for c in q.get("check", []))
    copy = (f'<button class="copy" data-copy="{E(after)}">수정 후 복사</button>' if after else "")
    return f"""
<article class="para" id="p-{E(q['id'])}" data-types="{E(' '.join(types))}" data-status="{E(q['status'])}">
 <header>
  <label class="done"><input type="checkbox" data-key="{E(q['id'])}"> 반영</label>
  <code>{E(q['id'])}</code> {badge(q['status'], status_kind(q['status']))} {badge(q.get('pattern', '-'), 'pat')}
  {copy}
 </header>
 <p class="summary"><b>요약</b> {E(q.get('summary', ''))}</p>
 <div class="cmp"><div><h5>수정 전</h5>{l}</div><div><h5>수정 후</h5>{r}</div></div>
 {f'<table class="edits"><thead><tr><th>유형</th><th>수정 전</th><th>수정 후</th><th>왜 바꾸는가</th></tr></thead><tbody>{edits}</tbody></table>' if edits else ''}
 {f'<div class="check"><b>저자 확인</b><ul>{checks}</ul></div>' if checks else ''}
</article>"""


def render_section(s: dict, src: dict) -> str:
    chain = "".join(
        f'<li><a href="#p-{E(q["id"])}"><code>{E(q["id"])}</code></a> {E(q.get("summary", ""))}</li>'
        for q in s["paras"] if q.get("after"))
    body = "".join(render_para(q, src) for q in s["paras"])
    return f"""
<section class="sec" id="s-{E(s['id'])}">
 <h3>{E(s['title'])}</h3>
 <div class="flow">
  <p><b>문단 구성 원칙</b> {E(s['pattern'])}</p>
  <p><b>흐름(수정 전)</b> {E(s['flow_before'])}</p>
  <p><b>흐름(수정 후)</b> {E(s['flow_after'])}</p>
  <p class="verdict"><b>판정</b> {E(s['verdict'])}</p>
  <details><summary>문단별 한 문장 요약 → 절 안의 논증 사슬</summary><ol>{chain}</ol></details>
 </div>
 {body}
</section>"""


def table(rows, head):
    th = "".join(f"<th>{E(h)}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{E(c)}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table class=grid><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>"


CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1f;--muted:#6b6b70;--card:#fff;--line:#e4e2dc;--accent:#2f5d8a;
--del-bg:#fde5e3;--del-fg:#9b1c12;--ins-bg:#e1f3e6;--ins-fg:#115c2a;--warn:#a15c00;--warn-bg:#fff3de;--chip:#eef2f7}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#17181b;--fg:#e8e6e1;--muted:#9a9aa0;--card:#202226;
--line:#33363c;--accent:#8fb6e0;--del-bg:#4a2320;--del-fg:#ffb4ab;--ins-bg:#1f3b28;--ins-fg:#a6e3b6;--warn:#f0b35a;--warn-bg:#3a2e17;--chip:#2a2f37}}
:root[data-theme="dark"]{--bg:#17181b;--fg:#e8e6e1;--muted:#9a9aa0;--card:#202226;--line:#33363c;--accent:#8fb6e0;
--del-bg:#4a2320;--del-fg:#ffb4ab;--ins-bg:#1f3b28;--ins-fg:#a6e3b6;--warn:#f0b35a;--warn-bg:#3a2e17;--chip:#2a2f37}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.7 "Pretendard","Noto Sans KR",system-ui,sans-serif}
.wrap{display:grid;grid-template-columns:250px 1fr;max-width:1500px;margin:0 auto}
nav{position:sticky;top:0;height:100vh;overflow:auto;padding:20px 14px;border-right:1px solid var(--line);font-size:13.5px}
nav a{display:block;color:var(--fg);text-decoration:none;padding:3px 6px;border-radius:5px}nav a:hover{background:var(--chip)}
nav .grp{margin:14px 0 4px;color:var(--muted);font-size:12px;letter-spacing:.04em}
main{padding:24px 28px 80px;min-width:0}h1{font-size:23px;margin:0 0 4px}h2{font-size:19px;margin:40px 0 12px;border-bottom:2px solid var(--fg);padding-bottom:4px}
h3{font-size:17px;margin:34px 0 10px;color:var(--accent)}h5{margin:0 0 6px;font-size:12px;color:var(--muted);letter-spacing:.05em}
.muted{color:var(--muted)}code{font:12.5px ui-monospace,Menlo,monospace;background:var(--chip);padding:1px 5px;border-radius:4px}
blockquote{margin:10px 0;padding:10px 14px;border-left:3px solid var(--accent);background:var(--card)}
.stats{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}.stat{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 12px}
.stat b{display:block;font-size:20px}
.toolbar{position:sticky;top:0;z-index:5;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.chip{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:2px 10px;font-size:12.5px;cursor:pointer}
.chip.on{background:var(--accent);color:var(--bg);border-color:var(--accent)}
.flow{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px;font-size:14px}.flow p{margin:4px 0}
.verdict{background:var(--warn-bg);padding:6px 8px;border-radius:6px}
.para{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:14px 0}
.para.isdone{opacity:.45}.para header{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.summary{margin:8px 0;font-size:14px}.summary b{color:var(--accent);margin-right:4px}
.cmp{display:grid;grid-template-columns:1fr 1fr;gap:12px}.cmp>div{border:1px solid var(--line);border-radius:8px;padding:8px 10px;min-width:0}
.cmp p{margin:0 0 8px}del{background:var(--del-bg);color:var(--del-fg);text-decoration:line-through}ins{background:var(--ins-bg);color:var(--ins-fg);text-decoration:none}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin:10px 0}th,td{border:1px solid var(--line);padding:5px 7px;vertical-align:top;text-align:left}
th{background:var(--chip);font-weight:600}.edits td.b{color:var(--del-fg)}.edits td.a{color:var(--ins-fg)}
.edits td:first-child{white-space:nowrap}
.badge{font-size:11.5px;padding:1px 7px;border-radius:999px;border:1px solid var(--line);white-space:nowrap}
.badge.edit{background:var(--chip)}.badge.keep{opacity:.7}.badge.del{background:var(--del-bg);color:var(--del-fg)}
.badge.warn{background:var(--warn-bg);color:var(--warn)}.badge.move{background:var(--ins-bg);color:var(--ins-fg)}.badge.pat{background:transparent}
.badge.type{background:var(--chip)}
.check{background:var(--warn-bg);border-radius:6px;padding:6px 10px;font-size:13.5px;margin-top:8px}.check ul{margin:4px 0 0 18px;padding:0}
button.copy{margin-left:auto;border:1px solid var(--accent);background:transparent;color:var(--accent);border-radius:6px;padding:2px 10px;cursor:pointer;font-size:12.5px}
button.copy.ok{background:var(--accent);color:var(--bg)}.done{font-size:12.5px;cursor:pointer}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}.box{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px}
.box pre{white-space:pre-wrap;font:13px/1.6 ui-monospace,Menlo,monospace;margin:0}
details summary{cursor:pointer;color:var(--accent);font-size:13.5px}
#theme{position:fixed;right:14px;bottom:14px;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:4px 12px;cursor:pointer}
@media (max-width:900px){.wrap{grid-template-columns:1fr}nav{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line)}
main{padding:16px}.cmp,.two{grid-template-columns:1fr}table{display:block;overflow-x:auto}}
"""

JS = """
const K='toego:'+document.title;let st={};try{st=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){}
const save=()=>{try{localStorage.setItem(K,JSON.stringify(st))}catch(e){}};
document.querySelectorAll('.done input').forEach(cb=>{const id=cb.dataset.key;cb.checked=!!st[id];
 const art=cb.closest('.para');art.classList.toggle('isdone',cb.checked);
 cb.onchange=()=>{st[id]=cb.checked;save();art.classList.toggle('isdone',cb.checked);count()}});
function count(){const n=document.querySelectorAll('.done input:checked').length,t=document.querySelectorAll('.done input').length;
 document.getElementById('prog').textContent=`반영 ${n}/${t}`}
document.querySelectorAll('button.copy').forEach(b=>b.onclick=async()=>{const t=b.dataset.copy;
 try{await navigator.clipboard.writeText(t)}catch(e){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove()}
 b.classList.add('ok');b.textContent='복사됨';setTimeout(()=>{b.classList.remove('ok');b.textContent=b.dataset.label||'수정 후 복사'},1200)});
let on=new Set(),hideDone=false,onlyChanged=false;
function apply(){document.querySelectorAll('.para').forEach(p=>{const ts=p.dataset.types.split(' ');
 let v=on.size===0||ts.some(t=>on.has(t));if(hideDone&&p.classList.contains('isdone'))v=false;
 if(onlyChanged&&p.dataset.status.startsWith('유지'))v=false;p.style.display=v?'':'none'})}
document.querySelectorAll('.chip[data-t]').forEach(c=>c.onclick=()=>{const t=c.dataset.t;on.has(t)?on.delete(t):on.add(t);c.classList.toggle('on');apply()});
document.getElementById('hidedone').onclick=e=>{hideDone=!hideDone;e.target.classList.toggle('on');apply()};
document.getElementById('theme').onclick=()=>{const r=document.documentElement,d=r.dataset.theme==='dark'||(!r.dataset.theme&&matchMedia('(prefers-color-scheme:dark)').matches);
 r.dataset.theme=d?'light':'dark'};
count();
"""


def build(review_path: Path, extract_dir: Path, out: Path) -> None:
    r = json.loads(review_path.read_text(encoding="utf-8"))
    src = {p["id"]: p for p in json.loads((extract_dir / "paragraphs.json").read_text(encoding="utf-8"))}
    m = r["meta"]
    all_p = [q for s in r["sections"] for q in s["paras"]]
    edits = [e for q in all_p for e in q.get("edits", [])]
    tcount = Counter(e["t"] for e in edits)
    scount = Counter(status_kind(q["status"]) for q in all_p)

    stats = "".join(f'<div class=stat><b>{v}</b>{E(k)}</div>' for k, v in [
        ("검토 문단", len(all_p)), ("수정 건수", len(edits)), ("사실관계·확인", scount["warn"]),
        ("삭제·병합", scount["del"]), ("신설·이동·분할", scount["move"]), ("저자 확인 항목", len(r["author_checks"]))])
    chips = "".join(f'<button class=chip data-t="{E(t)}">{E(t)} {n}</button>' for t, n in tcount.most_common())

    nav_secs = "".join(f'<a href="#s-{E(s["id"])}">{E(s["title"])}</a>' for s in r["sections"])
    nav = f"""<nav><div class=grp>개요</div><a href="#top">심사 의견과 판정 기준</a><a href="#structure">7. 장·절 구조</a>
<a href="#global">5. 전체 흐름과 결론</a><a href="#abstract">6. 영문 초록</a><div class=grp>1-4. 본문 퇴고</div>{nav_secs}
<div class=grp>부록</div><a href="#captions">캡션·표</a><a href="#refs">참고문헌</a><a href="#checks">저자 확인 사항</a><a href="#facts">사실 대조 기록</a></nav>"""

    rl = r["rules"]
    rules = (f"<h3>시제 규칙</h3>{table(rl['tense'], ['위치', '시제', '예'])}"
             f"<h3>문단 구성(두괄·미괄·양괄) 규칙</h3>{table(rl['structure'], ['위치', '형식', '이유'])}"
             f"<h3>수정 유형</h3>{table(rl['flags'], ['유형', '뜻'])}")

    st = r["structure"]
    structure = f"""<h2 id=structure>7. 장·절 구조</h2><div class=two>
<div class=box><h5>현재</h5><pre>{E(chr(10).join(st['before']))}</pre></div>
<div class=box><h5>제안</h5><pre>{E(chr(10).join(st['after']))}</pre></div></div>
{table(st['reasons'], ['변경', '왜'])}"""

    g = r["global_flow"]
    glob = f"""<h2 id=global>5. 전체 흐름이 결론에 드러나는가</h2>
{table(g['question_to_conclusion'], ['서론이 제기한 질문', '본문 근거', '결론 반영'])}
<p class=verdict><b>판정</b> {E(g['verdict'])}</p>
<details open><summary>수정 후 문단 요약의 전체 사슬</summary><p>{E(g['paragraph_chain'])}</p></details>"""

    a = r["abstract"]
    la, ra = word_diff(a["before"], a["after"])
    aedits = "".join(f"<tr><td>{badge(e['t'], 'type')}</td><td class=b>{E(e['b'])}</td><td class=a>{E(e['a'])}</td><td>{E(e['why'])}</td></tr>" for e in a["edits"])
    abstract = f"""<h2 id=abstract>6. 영문 초록</h2>
<article class=para id="p-ABSTRACT" data-types="{E(' '.join(sorted({e['t'] for e in a['edits']})))}" data-status="수정">
<header><label class=done><input type=checkbox data-key="ABSTRACT"> 반영</label><code>ABSTRACT</code>{badge('수정', 'edit')}
<button class=copy data-copy="{E(a['after'])}">수정 후 복사</button></header>
<div class=cmp><div><h5>수정 전</h5><p>{la}</p></div><div><h5>수정 후</h5><p>{ra}</p></div></div>
<table class=edits><thead><tr><th>유형</th><th>수정 전</th><th>수정 후</th><th>왜 바꾸는가</th></tr></thead><tbody>{aedits}</tbody></table>
<p class=muted>{E(a['note'])}</p></article>"""

    caps = table([[c["target"], c["before"], c["after"], c["why"]] for c in r["captions"]], ["대상", "수정 전", "수정 후", "왜"])
    refs = table([[x["ref"], x["issue"], x["fix"]] for x in r["references"]], ["번호", "문제", "수정"])
    checks = "<ol>" + "".join(f"<li>{E(c)}</li>" for c in r["author_checks"]) + "</ol>"
    facts = table(r["fact_checks"], ["대조 항목", "결과", "출처"])
    evid = "<ul>" + "".join(f"<li><code>{E(x)}</code></li>" for x in m["evidence_sources"]) + "</ul>"

    body = "".join(render_section(s, src) for s in r["sections"])
    doc = f"""<!doctype html><html lang=ko><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>{E(m['title'])}</title><style>{CSS}</style></head><body><div class=wrap>{nav}<main>
<h1 id=top>{E(m['title'])}</h1><p class=muted>원고: <code>{E(m['source'])}</code> · 검토일 {E(m['date'])}</p>
<blockquote><b>심사 의견</b><br>{E(m['reviewer_comment'])}</blockquote>
<div class=stats>{stats}</div>
<details><summary>검토에 사용한 근거 자료</summary>{evid}</details>
<details><summary>판정 기준 — 시제·문단 구성·수정 유형</summary>{rules}</details>
{structure}{glob}{abstract}
<h2>1-4. 본문 퇴고 (문장 → 문단 → 절)</h2>
<p class=muted>각 문단: 수정 전(빨강 = 삭제) / 수정 후(초록 = 추가), ‘수정 후 복사’로 한/글에 바로 붙여넣기. 수식 개체([원문 수식])와 인용 번호는 원문 개체를 유지할 것. ‘반영’ 체크는 이 브라우저에 저장된다.</p>
<div class=toolbar><span class=muted>유형 필터</span>{chips}<button class=chip id=hidedone>반영 완료 숨기기</button><span id=prog class=muted></span></div>
{body}
<h2 id=captions>캡션·표</h2>{caps}<h2 id=refs>참고문헌</h2>{refs}
<h2 id=checks>저자 확인 사항</h2>{checks}<h2 id=facts>사실 대조 기록</h2>{facts}
</main></div><button id=theme>테마</button><script>{JS}</script></body></html>"""
    out.write_text(doc, encoding="utf-8")
    print(f"{out}  ({len(doc)//1024} KB, 문단 {len(all_p)}, 수정 {len(edits)})")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    build(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
