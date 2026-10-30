#!/usr/bin/env python3
"""细纲校验（S4 门禁）：必填字段、窗口连续性、与卷纲事件链的覆盖关系。"""
import argparse, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

PLACEHOLDER = ("待填", "待定", "（", "(")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--from", dest="start", type=int, default=None)
    ap.add_argument("--to", dest="end", type=int, default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = a.project.rstrip("/")
    chaps = [n for n, _ in lib.chapter_files(root)]
    start = a.start or (max(chaps) + 1 if chaps else 1)
    end = a.end or start + 9

    problems, ok = [], []
    missing = []
    for n in range(start, end + 1):
        o = lib.outline(root, n)
        if o is None: missing.append(n); continue
        f = o["fields"]
        for k in ("目标", "冲突", "信息增量", "钩子", "字数", "功能"):
            v = f.get(k, "")
            if not v or v.startswith(PLACEHOLDER): problems.append(f"第{n}章：字段「{k}」缺失或仍是占位符")
        if not o["points"]: problems.append(f"第{n}章：没有「## 要点」编号列表")
        for p in o["points"]:
            if p.startswith(PLACEHOLDER): problems.append(f"第{n}章：要点仍是占位符「{p[:12]}…」")
        ok.append(n)
    if missing:
        problems.append("缺细纲的章号：" + ", ".join(map(str, missing)))

    # 事件覆盖：每个卷纲事件至少被一章要点覆盖
    evs, unmatched = [], []
    for f in sorted(__import__("glob").glob(os.path.join(root, "大纲", "10-卷纲-卷*.md"))):
        sec = re.search(r"##\s*主要事件链.*?\n(.*?)(?:\n##|\Z)", lib.read(f), re.S)
        if sec:
            evs += [m.group(1).strip() for m in
                    (re.match(r"^\s*\d+[.、)]\s*(.+)$", l) for l in sec.group(1).split("\n")) if m]
    per_ch = []
    for n in ok:
        o = lib.outline(root, n)
        if o: per_ch.append((n, o["fields"].get("目标", "") + " " + " ".join(o["points"])))
    for e in evs:
        if not any(lib.overlap(e, txt) >= 0.3 or e in txt for _, txt in per_ch):
            unmatched.append(e)

    res = {"range": [start, end], "checked": len(ok), "missing": missing,
           "problems": problems, "events": len(evs), "unmatched_events": unmatched,
           "pass": not problems and not unmatched}
    human = [f"细纲校验 {start}–{end}：{len(ok)} 份，问题 {len(problems)} 项"]
    human += ["  ✗ " + p for p in problems[:12]]
    if unmatched:
        human.append(f"  ✗ 有 {len(unmatched)} 个卷纲事件没落到细纲要点：" + "；".join(x[:16] for x in unmatched[:5]))
    human.append("  ✓ 通过" if res["pass"] else "  → 先补齐细纲再写正文")
    lib.emit(res, a.json, "\n".join(human))
    return 0 if res["pass"] else 1

if __name__ == "__main__":
    sys.exit(main())
