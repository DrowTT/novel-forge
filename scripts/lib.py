"""novel-forge 共享解析层：项目/细纲/追踪/文本度量。仅标准库。"""
from __future__ import annotations
import glob, json, os, re, sys, unicodedata
from dataclasses import dataclass, field

CHAP_RE = re.compile(r"第\s*(\d+)\s*章")

def read(p: str) -> str:
    return open(p, encoding="utf-8").read() if os.path.isfile(p) else ""

def write(p: str, s: str) -> None:
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)

def cjk_count(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text)) + len(re.findall(r"[A-Za-z0-9]+", text))

def strip_h1(text: str) -> str:
    return re.sub(r"^\s*#\s*.+\n+", "", text, count=1)

def _norm(text: str) -> str:
    return "".join(ch for ch in text
                   if not ch.isspace() and not unicodedata.category(ch).startswith("P"))

def bigrams(text: str) -> set[str]:
    t = _norm(text)
    return {t[i:i+2] for i in range(len(t) - 1)}

def overlap(a: str, b: str) -> float:
    """a 被 b 覆盖的比例（0–1）。"""
    A, B = bigrams(a), bigrams(b)
    if not A: return 0.0
    return len(A & B) / len(A)

def shingles(text: str, n: int = 8) -> set[str]:
    t = _norm(text)
    return {t[i:i+n] for i in range(max(0, len(t) - n + 1))}

def chapter_files(root: str) -> list[tuple[int, str]]:
    files = glob.glob(os.path.join(root, "正文", "*.md"))
    if not files:
        files = [f for f in glob.glob(os.path.join(root, "第*.md")) if "成品" not in f]
    out = []
    for f in files:
        m = CHAP_RE.search(os.path.basename(f))
        if m: out.append((int(m.group(1)), f))
    return sorted(out)

def project_meta(root: str) -> dict:
    meta = {}
    for line in read(os.path.join(root, "项目.md")).split("\n"):
        m = re.match(r"^-\s*([^：:]+)[：:]\s*(.+?)\s*$", line)
        if m: meta[m.group(1).strip()] = m.group(2).strip()
    return meta

def table_rows(path: str) -> list[list[str]]:
    rows = []
    for line in read(path).split("\n"):
        s = line.strip()
        if not s.startswith("|") or "---" in s: continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        rows.append(cells)
    return rows[1:] if rows else []   # 去表头

def outline(root: str, num: int) -> dict | None:
    p = os.path.join(root, "大纲", "细纲", f"第{num:03d}章.md")
    if not os.path.isfile(p):
        cand = glob.glob(os.path.join(root, "大纲", "细纲", f"第{num}章*.md"))
        if not cand: return None
        p = cand[0]
    t = read(p)
    d = {"path": p, "fields": {}, "points": []}
    for line in t.split("\n"):
        m = re.match(r"^-\s*(目标|冲突|信息增量|出场|钩子|字数|功能)[：:]\s*(.*)$", line.strip())
        if m: d["fields"][m.group(1)] = m.group(2).strip()
    sec = re.search(r"##\s*要点\s*\n(.*?)(?:\n##|\Z)", t, re.S)
    if sec:
        d["points"] = [re.sub(r"^\d+[.、)]\s*", "", l).strip()
                        for l in sec.group(1).split("\n")
                        if re.match(r"^\s*\d+[.、)]", l)]
    return d

def foreshadow(root: str) -> list[dict]:
    out = []
    for r in table_rows(os.path.join(root, "追踪", "伏笔.md")):
        if len(r) < 6 or not r[0] or r[0] == "编号": continue
        try: plan = int(re.sub(r"\D", "", r[4]) or 0)
        except ValueError: plan = 0
        out.append({"id": r[0], "planted": r[1], "text": r[2], "target": r[3],
                    "plan_ch": plan, "status": r[5]})
    return out

def release(root: str) -> list[dict]:
    out = []
    for r in table_rows(os.path.join(root, "追踪", "发布.md")):
        if len(r) < 2 or not r[0]: continue
        m = CHAP_RE.search(r[0]) or re.match(r"^(\d+)$", r[0])
        if not m: continue
        out.append({"num": int(m.group(1)), "status": r[1],
                    "date": r[2] if len(r) > 2 else "",
                    "read": r[3] if len(r) > 3 else "",
                    "finish": r[4] if len(r) > 4 else ""})
    return out

HOOK_SIGNALS = [
    (r"[？?]\s*$", "悬念"),
    (r"(突然|忽然|就在这时|猛地|陡然)", "危机"),
    (r"(不是|却|但|然而|可它|结果)", "反转"),
    (r"(血|尸体|尖叫|枪声|脚步|敲门|拖|腥)", "危机"),
    (r"(门.{0,4}(开|响)|有人|影子|眼睛)", "悬念"),
]

def hook_type(text: str) -> str:
    tail = strip_h1(text).strip()[-260:]
    for pat, kind in HOOK_SIGNALS:
        if re.search(pat, tail): return kind
    return "无"

def emit(obj, as_json: bool, human: str) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2) if as_json else human)
