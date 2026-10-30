#!/usr/bin/env python3
"""断点记账（S5-5）：更新 项目.md 进度、追加 CHANGELOG、快照一份成品。"""
import argparse, datetime, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib, export_novel

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--note", default="")
    ap.add_argument("--no-snapshot", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = a.project.rstrip("/")
    chaps = lib.chapter_files(root)
    total = sum(lib.cjk_count(lib.strip_h1(lib.read(f))) for _, f in chaps)
    rows = lib.release(root)
    buffer = len([r for r in rows if "存稿" in r["status"] or "已排期" in r["status"]])
    last = chaps[-1][0] if chaps else 0
    today = datetime.date.today().isoformat()

    meta_p = os.path.join(root, "项目.md")
    t = lib.read(meta_p)
    prog = f"- 当前进度：已写 {last} 章 / {total} 字，存稿 {buffer} 章（checkpoint {today}）"
    if re.search(r"^- 当前进度：.*$", t, re.M): t = re.sub(r"^- 当前进度：.*$", prog, t, count=1, flags=re.M)
    else: t = t.rstrip() + "\n" + prog + "\n"
    nxt = f"- 下一交付：第{last+1}章（先跑 context_brief.py）"
    if re.search(r"^- 下一交付：.*$", t, re.M): t = re.sub(r"^- 下一交付：.*$", nxt, t, count=1, flags=re.M)
    else: t = t.rstrip() + "\n" + nxt + "\n"
    lib.write(meta_p, t)

    log = os.path.join(root, "CHANGELOG.md")
    prev = lib.read(log) or "# CHANGELOG\n\n"
    line = f"- {today} 写到第{last}章（{total} 字，存稿 {buffer} 章）" + (f"：{a.note}" if a.note else "")
    lib.write(log, prev.rstrip() + "\n" + line + "\n")

    snap = None
    if not a.no_snapshot and chaps:
        snap = os.path.join(root, "成品", "snapshots", f"{os.path.basename(root)}-ch{last:03d}.md")
        export_novel.build(root, snap)
    res = {"chapter": last, "words": total, "buffer": buffer, "snapshot": snap, "date": today}
    lib.emit(res, a.json, f"checkpoint：第{last}章 / {total} 字 / 存稿 {buffer} 章" + (f"，快照 {snap}" if snap else ""))
    return 0

if __name__ == "__main__":
    sys.exit(main())
