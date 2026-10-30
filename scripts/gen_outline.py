#!/usr/bin/env python3
"""批量生成细纲骨架（S4）：从卷纲事件链分配事件，写 大纲/细纲/第NNN章.md。"""
import argparse, glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

FUNC_CYCLE = ["推进", "铺垫", "爽点", "情感", "推进"]

def vol_events(root, vol=None):
    files = sorted(glob.glob(os.path.join(root, "大纲", "10-卷纲-卷*.md")))
    if vol: files = [f for f in files if f"卷{vol}" in f] or files
    ev = []
    for f in files:
        t = lib.read(f)
        sec = re.search(r"##\s*主要事件链.*?\n(.*?)(?:\n##|\Z)", t, re.S)
        if not sec: continue
        for line in sec.group(1).split("\n"):
            m = re.match(r"^\s*\d+[.、)]\s*(.+)$", line)
            if m and m.group(1).strip(): ev.append(m.group(1).strip())
    return ev

def cast(root):
    t = lib.read(os.path.join(root, "设定", "人设.md"))
    names = re.findall(r"姓名[：:]\s*([^\s/，,、]+)", t)
    names += [c for c in re.findall(r"^\|\s*([^\s|]{2,6})\s*\|", t, re.M)]
    out = []
    for n in names:
        if n not in out and n not in {"姓名", "名字"}: out.append(n)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--from", dest="start", type=int, required=True)
    ap.add_argument("--to", dest="end", type=int, required=True)
    ap.add_argument("--vol", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root, meta = a.project.rstrip("/"), lib.project_meta(a.project)
    per = int(re.sub(r"\D", "", meta.get("单章目标", "2500")) or 2500)
    events = vol_events(root, a.vol)
    people = cast(root)
    created, skipped = [], []

    d = os.path.join(root, "大纲", "细纲")
    os.makedirs(d, exist_ok=True)
    for i, n in enumerate(range(a.start, a.end + 1)):
        p = os.path.join(d, f"第{n:03d}章.md")
        if os.path.exists(p) and not a.force:
            skipped.append(n); continue
        ev = events[i % len(events)] if events else "（待填：本章核心事件）"
        body = f"""# 第{n:03d}章

- 目标: {ev}
- 冲突: （待填：谁拦着，为什么不能退）
- 信息增量: （待填：读者本章新知道的事）
- 出场: {("、".join(people[:3]) if people else "（待填）")}
- 钩子: （待定：悬念/危机/反转）
- 字数: {per}
- 功能: {FUNC_CYCLE[i % len(FUNC_CYCLE)]}

## 要点
1. {ev}
2. （待填：具体场面/冲突升级）
3. （待填：本章钩子落点）
"""
        lib.write(p, body)
        created.append(n)
    res = {"created": created, "skipped": skipped, "events": len(events), "dir": d}
    lib.emit(res, a.json, f"已生成 {len(created)} 份细纲 → {d}" + (f"，跳过 {len(skipped)} 份已存在" if skipped else "")
             + ("" if events else "\n警告：卷纲里没找到「## 主要事件链」编号列表，细纲里的目标都是占位符"))
    return 0

if __name__ == "__main__":
    sys.exit(main())
