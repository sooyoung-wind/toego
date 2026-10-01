"""퇴고 1차 선별기 — 사람이(또는 에이전트가) 읽기 전에 기계적으로 잡을 수 있는 것만 잡는다.

판정을 내리지 않는다. "여기를 보라"는 표시만 한다. 과잉일반화 어휘가 있어도 수치로 뒷받침되면
문제가 아니고, 과거형이 아니어도 일반 사실이면 현재형이 맞다. 최종 판단은 문맥을 읽는 쪽이 한다.

규칙 묶음
    typo        알려진 오탈자·잘못된 조사 (사전 기반)
    overclaim   단정·과장 어휘 — 수치 근거가 같은 문장에 있는지 확인할 것
    ai_style    번역투·상투 표현 — 내용 없이 문장을 늘리는 경우가 많다
    tense       절 위치 대비 시제 후보 (방법·결과 절의 현재형 서술 종결)
    unit        숫자-단위 붙여쓰기, 표기 혼용
    repeat      한 문단 안에서 같은 접속어가 2회 이상 문두에 쓰인 경우
    xref        Fig./Table 첫 인용 순서가 번호 순서와 다른 경우, 캡션과 본문 불일치 후보

실행:
    uv run --frozen --quiet --no-project python ${CLAUDE_SKILL_DIR}/scripts/lint_ko.py <extract_dir> > lint.json
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

TYPO = {
    "정량적으로 않은": "정량적으로 평가되지 않은", "경에는": "경우에는", "영약": "영역",
    "레포드": "레코드", "잉용": "이용", "계측은": "계층은", "표분": "표본", "졍규": "정규",
    "외곡": "왜곡", "아치를": "차이를", "지단 지표": "진단 지표", "Ouput": "Output",
    "experiment은": "experiment는", "분위수임이 알 수": "분위수임을 알 수",
}
OVERCLAIM = ["매우", "정확히", "완벽", "일관되게", "능가", "입증", "신뢰성 있게", "정밀하게",
             "핵심", "다각도", "널리", "크게", "모두에서", "전 풍속", "항상", "극대화", "충실한",
             "확보하였다", "demonstrate", "prove"]
AI_STYLE = ["종합적으로", "다양한", "이러한 결과는", "측면에서", "관점에서", "구조적", "효과적",
            "~을 통해", "을 통해", "를 통해", "라는 점이다", "시사한다", "의미한다", "가능성을 제시",
            "기여할 수", "활용될 수 있다", "중요하다", "필요하다", "하게 된다", "존재하게 된다"]
CONNECTIVES = ["따라서", "이는", "이러한", "또한", "반면", "즉", "그러나", "특히", "이처럼"]
# 방법·결과 절에서 수행 사실을 현재형으로 끝낸 후보. 정의·일반 사실이면 현재형이 맞다.
PRESENT_END = re.compile(r"(한다|된다|진다|준다|난다|인다|는다)\.$")
PAST_SECTIONS = re.compile(r"^(2|3)\.")
UNIT = [(re.compile(r"\d(m|ms|MW|Hz|㎐|%)\b"), "숫자와 단위 사이 공백"),
        (re.compile(r"\d\s+–|–\s+\d|\d\s+-\s+\d"), "범위 기호 앞뒤 공백")]


def lint(extract_dir: Path) -> dict:
    paras = json.loads((extract_dir / "paragraphs.json").read_text(encoding="utf-8"))
    cap_file = extract_dir / "captions.json"
    captions = json.loads(cap_file.read_text(encoding="utf-8")) if cap_file.exists() else []
    findings = []

    def add(pid, rule, hit, sent):
        findings.append({"para": pid, "rule": rule, "hit": hit, "sentence": sent})

    for p in paras:
        starts = Counter()
        for s in p["sentences"]:
            for k, v in TYPO.items():
                if k in s:
                    add(p["id"], "typo", f"{k} → {v}", s)
            for w in OVERCLAIM:
                if w in s:
                    add(p["id"], "overclaim", w, s)
            for w in AI_STYLE:
                if w in s:
                    add(p["id"], "ai_style", w, s)
            if PAST_SECTIONS.match(p["section"]) and PRESENT_END.search(s):
                add(p["id"], "tense", PRESENT_END.search(s).group(1), s)
            for rx, msg in UNIT:
                if rx.search(s):
                    add(p["id"], "unit", msg, s)
            for c in CONNECTIVES:
                if s.startswith(c):
                    starts[c] += 1
        for c, n in starts.items():
            if n >= 2:
                add(p["id"], "repeat", f"문두 '{c}' {n}회", "")

    # 첫 인용 순서
    first = {}
    for p in paras:
        for kind, num in re.findall(r"(Fig\.?|Table)\s*(\d+)", p["text"]):
            key = ("Fig" if kind.startswith("Fig") else "Table", int(num))
            first.setdefault(key, p["id"])
    for kind in ("Fig", "Table"):
        order = [n for (k, n) in first if k == kind]
        if order != sorted(order):
            add("-", "xref", f"{kind} 첫 인용 순서 {order}", "")
    cap = {}
    for c in captions:
        m = re.match(r"(Fig|Table)\.?\s*(\d+)(.*)", c)
        if m:
            cap[(m.group(1), int(m.group(2)))] = m.group(3).strip()
    for (k, n), pid in first.items():
        if (k, n) not in cap:
            add(pid, "xref", f"{k}. {n} 캡션 없음", "")

    summary = Counter(f["rule"] for f in findings)
    return {"summary": dict(summary), "captions": cap and {f"{k} {n}": v for (k, n), v in cap.items()},
            "first_citation": {f"{k} {n}": v for (k, n), v in first.items()}, "findings": findings}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    res = lint(Path(sys.argv[1]))
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res["summary"], ensure_ascii=False), file=sys.stderr)
