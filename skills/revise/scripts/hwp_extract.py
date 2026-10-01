"""HWP 원고를 퇴고용 구조 데이터로 푼다.

hwp5txt 는 본문 문단을, hwp5html 은 표·초록·캡션을 잘 꺼낸다. 둘 다 필요하므로 두 번 변환한다.
수식 개체는 텍스트로 나오지 않는다 — 본문에 "(3)" 같은 번호만 남는다. 퇴고 대상은 문장이므로
그대로 두고, 수식 기호가 빠진 자리는 사람이 원본과 대조한다.

출력 (out_dir):
    source.txt        hwp5txt 원문
    html/             hwp5html 결과 (그림 bindata 포함)
    paragraphs.json   [{id, section, text, sentences[]}]
    tables.json       [{index, rows[[cell]]}]  — 0번은 표제·초록 머리 표
    captions.json     [str]

실행:
    uv run --frozen --quiet --no-project --python 3.11 --with pyhwp==0.1b15 --with six==1.17.0 \
        --with lxml==6.1.3 --with beautifulsoup4==4.15.0 \
        python ${CLAUDE_SKILL_DIR}/scripts/hwp_extract.py <원고.hwp> <out_dir>

.hwp(HWP 5.x 바이너리)만 지원한다. .hwpx 는 한/글에서 .hwp 로 다시 저장해서 넣는다.
"""
import json
import re
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

from bs4 import BeautifulSoup

warnings.filterwarnings("ignore")

HEADING = re.compile(r"^(\d+(?:\.\d+){1,2})\s+(\S.*)$|^(\d+)\.\s+(\S.*)$")
# 한국어 학술문 종결: '~다.' 뒤 공백/괄호. 소수점·약어(Fig. 3)는 끊지 않는다.
SENT_END = re.compile(r"(?<=[다\]\)]\.)\s+|(?<=다\.)(?=\()")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in SENT_END.split(text) if s.strip()]


def parse_body(txt: str) -> list[dict]:
    paras, section, counter = [], "front", {}
    for raw in txt.splitlines():
        line = raw.strip()
        if not line or line in ("<표>", "<그림>"):
            continue
        m = HEADING.match(line)
        if m and len(line) < 40:
            section = m.group(1) or m.group(3)
            continue
        if re.fullmatch(r"\(\d+\)", line):  # 수식 번호만 남은 줄
            continue
        counter[section] = counter.get(section, 0) + 1
        paras.append({
            "id": f"{section}-P{counter[section]}",
            "section": section,
            "text": line,
            "sentences": split_sentences(line),
        })
    return paras


def parse_html(xhtml: Path) -> tuple[list[dict], list[str]]:
    soup = BeautifulSoup(xhtml.read_text(encoding="utf-8"), "lxml")
    tables = []
    for t in soup.find_all("table"):
        if t.find_parent("table"):
            continue
        rows = [[c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"], recursive=False)]
                for tr in t.find_all("tr")]
        tables.append({"index": len(tables), "rows": rows})
    captions = []
    for p in soup.find_all("p"):
        s = p.get_text("", strip=True)
        if re.match(r"^(Fig\.|Table)\s*\d", s) and len(s) < 250:
            captions.append(s)
    return tables, captions


def main(src: str, out: str) -> None:
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    local = out_dir / "src.hwp"  # 경로에 한글·공백이 있으면 pyhwp 가 가끔 실패한다
    if Path(src).resolve() != local.resolve():
        shutil.copyfile(src, local)

    txt = subprocess.run(["hwp5txt", str(local)], capture_output=True, text=True, check=True).stdout
    (out_dir / "source.txt").write_text(txt, encoding="utf-8")
    subprocess.run(["hwp5html", "--output", str(out_dir / "html"), str(local)],
                   capture_output=True, check=True)

    paras = parse_body(txt)
    tables, captions = parse_html(out_dir / "html" / "index.xhtml")
    for name, obj in (("paragraphs", paras), ("tables", tables), ("captions", captions)):
        (out_dir / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    n_sent = sum(len(p["sentences"]) for p in paras)
    # 입력 전제: 저자 정보를 뺀 심사용 원고. 이메일이 보이면 사용자에게 알린다.
    emails = set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", txt + json.dumps(tables, ensure_ascii=False)))
    if emails:
        print(f"WARNING: 원고에 이메일 주소 {len(emails)}개가 있습니다. 저자 정보를 지운 심사용 원고를 넣어 주세요.",
              file=sys.stderr)
    print(f"paragraphs={len(paras)} sentences={n_sent} tables={len(tables)} captions={len(captions)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
