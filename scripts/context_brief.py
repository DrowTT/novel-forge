#!/usr/bin/env python3
"""写前简报（S5-1）：前文尾部 + 细纲 + 伏笔(含逾期) + 状态 + 硬约束 + 卷级远景。"""
import argparse, glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

def tail(text, n=700):
    return re.sub(r"\s+", " ", lib.strip_h1(text)).strip()[-n:]

def vol_scope(root, n):
    vols = sorted(glob.glob(os.path.join(root, "大纲", "10-卷纲-卷*.md")))
    cur = None
    for v in vols:
        t = lib.read(v)
        m = re.search(r"章节范围[：:]\s*(\d+)\s*[-–~]\s*(\d+)", t)
        if m and int(m.group(1)) <= n <= int(m.group(2)): cur = (v, t); break
    if cur is None and vols: cur = (vols[-1], lib.read(vols[-1]))
    if cur is None: return None
    v, t = cur
    goal = re.search(r"##\s*本卷目标\s*\n(.*?)(?:\n##|\Z)", t, re.S)
    return {"file": os.path.basename(v),
            "goal": goal.group(1).strip() if goal else "（未写本卷目标）"}

def milestones(root):
    t = lib.read(os.path.join(root, "大纲", "00-总纲.md"))
    sec = re.search(r"##\s*主线里程碑.*?\n(.*?)(?:\n##|\Z)", t, re.S)
    return [re.sub(r"^\s*[-*\d.、)]+\s*", "", l).strip()
            for l in sec.group(1).split("\n") if l.strip()] if sec else []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--chapter", type=int, default=None)
    ap.add_argument("--tail", type=int, default=700)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = a.project.rstrip("/")
    chaps = lib.chapter_files(root)
    nxt = a.chapter or ((chaps[-1][0] + 1) if chaps else 1)
    meta = lib.project_meta(root)

    brief = {"chapter": nxt, "project": meta, "prev": [], "outline": None,
             "foreshadow_open": [], "foreshadow_overdue": [], "status": "", "rules": "",
             "volume": None, "milestones": []}

    for num, f in chaps[-2:]:
        brief["prev"].append({"chapter": num, "tail": tail(lib.read(f), a.tail)})

    o = lib.outline(root, nxt)
    if o: brief["outline"] = {"fields": o["fields"], "points": o["points"]}

    for r in lib.foreshadow(root):
        if "未回收" not in r["status"] and "未埋" not in r["status"]: continue
        brief["foreshadow_open"].append(r)
        if 0 < r["plan_ch"] < nxt: brief["foreshadow_overdue"].append(r)

    st = lib.table_rows(os.path.join(root, "追踪", "状态.md"))
    brief["status"] = " | ".join(st[-1]) if st else ""

    rules = re.search(r"##\s*规则.*?\n(.*?)(?:\n##|\Z)",
                      lib.read(os.path.join(root, "设定", "世界观.md")), re.S)
    brief["rules"] = rules.group(1).strip() if rules else ""
    brief["volume"] = vol_scope(root, nxt)
    brief["milestones"] = milestones(root)

    if a.json:
        lib.emit(brief, True, "")
        return 0
    L = [f"# 写前简报：{os.path.basename(root)} 第 {nxt} 章", ""]
    L += [f"- {k}：{v}" for k, v in list(meta.items())[:7]] + [""]
    if brief["volume"]:
        L += [f"## 卷级远景（{brief['volume']['file']}）", brief["volume"]["goal"], ""]
    if brief["milestones"]:
        L += ["## 主线里程碑"] + [f"- {m}" for m in brief["milestones"]] + [""]
    if brief["outline"]:
        f = brief["outline"]["fields"]
        L += ["## 本章细纲", f"- 目标：{f.get('目标','')}", f"- 冲突：{f.get('冲突','')}",
              f"- 信息增量：{f.get('信息增量','')}", f"- 钩子：{f.get('钩子','')}",
              f"- 功能/字数：{f.get('功能','')} / {f.get('字数','')}"]
        L += [f"{i}. {p}" for i, p in enumerate(brief["outline"]["points"], 1)] + [""]
    else:
        L += ["## 本章细纲", "（无：先跑 gen_outline.py 出细纲，不要没有细纲就写正文）", ""]
    if brief["prev"]:
        for p in brief["prev"]:
            L += [f"## 前文尾部：第{p['chapter']}章", p["tail"], ""]
    else:
        L += ["## 前文尾部：无（开篇章）", ""]
    L += ["## 未回收伏笔"]
    L += [f"- {r['id']}（埋于第{r['planted']}章 → 计划第{r['plan_ch']}章回收）：{r['text']}"
          for r in brief["foreshadow_open"]] or ["（无）"]
    if brief["foreshadow_overdue"]:
        L += ["", "### ⚠ 逾期未回收"]
        L += [f"- {r['id']}：计划第{r['plan_ch']}章回收，已逾期到第{nxt}章 —— 本章或下章必须处理" for r in brief["foreshadow_overdue"]]
    L += ["", "## 最近状态", brief["status"] or "（无）", "",
          "## 硬约束", brief["rules"] or "（未填写：先写 设定/世界观.md 的规则）"]
    print("\n".join(L))
    return 0

if __name__ == "__main__":
    sys.exit(main())
