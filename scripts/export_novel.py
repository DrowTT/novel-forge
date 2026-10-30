#!/usr/bin/env python3
"""合并成品：正文 → 成品/<书名>.md（标题页 + 目录带字数 + 正文）。"""
import argparse, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

def build(root, out):
    title = os.path.basename(root)
    chaps = lib.chapter_files(root)
    if not chaps: raise SystemExit(f"没有章节：{root}")
    meta = lib.project_meta(root)
    intro = ""
    m = re.search(r"##\s*(?:一句话故事|简介)\s*\n+(.+?)(?:\n#|\Z)",
                  lib.read(os.path.join(root, "项目.md")), re.S)
    if m and not m.group(1).strip().startswith("（"): intro = m.group(1).strip()
    stats, bodies = [], []
    for n, f in chaps:
        body = lib.strip_h1(lib.read(f)).strip()
        h1 = re.search(r"^#\s+(.+)$", lib.read(f), re.M)
        name = h1.group(1).strip() if h1 else os.path.basename(f)[:-3]
        stats.append((name, lib.cjk_count(body))); bodies.append((name, body))
    L = [f"# {title}", ""]
    if meta.get("题材"): L += [f"> {meta.get('题材')} ｜ {meta.get('形态','')} ｜ {sum(s[1] for s in stats)} 字", ""]
    if intro: L += ["## 简介", "", intro, ""]
    L += ["## 目录", ""] + [f"{i}. {nm}（{w} 字）" for i, (nm, w) in enumerate(stats, 1)] + ["", "---", ""]
    for nm, body in bodies: L += [f"## {nm}", "", body, "", "---", ""]
    lib.write(out, "\n".join(L).rstrip() + "\n")
    return stats

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--snapshot", action="store_true", help="写到 成品/snapshots/ 而不是覆盖成品")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = a.project.rstrip("/")
    title = os.path.basename(root)
    out = a.out or os.path.join(root, "成品", f"{title}.md")
    if a.snapshot:
        n = len(lib.chapter_files(root))
        out = os.path.join(root, "成品", "snapshots", f"{title}-ch{n:03d}.md")
    stats = build(root, out)
    total = sum(w for _, w in stats)
    short = [(nm, w) for nm, w in stats if w < 1500]
    res = {"out": out, "chapters": len(stats), "words": total, "short": short}
    human = [f"已导出：{out}", f"章节 {len(stats)}  总字数 {total}  平均 {total//max(len(stats),1)}"]
    if short: human.append("偏短章节：" + ", ".join(f"{nm}({w})" for nm, w in short))
    lib.emit(res, a.json, "\n".join(human))
    return 0

if __name__ == "__main__":
    sys.exit(main())
