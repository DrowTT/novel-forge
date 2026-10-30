#!/usr/bin/env python3
"""成品自检（S7）：章号连续、标题一致、字数分布、伏笔逾期、成品与正文同步。"""
import argparse, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = a.project.rstrip("/")
    meta = lib.project_meta(root)
    per = int(re.sub(r"\D", "", meta.get("单章目标", "2500")) or 2500)
    chaps = lib.chapter_files(root)
    p0, p1 = [], []

    nums = [n for n, _ in chaps]
    if nums:
        expect = list(range(nums[0], nums[-1] + 1))
        if nums != expect:
            miss = [n for n in expect if n not in nums]
            dup = [n for n in set(nums) if nums.count(n) > 1]
            p0.append(f"章号不连续：缺 {miss}，重复 {dup}")
    else:
        p0.append("没有找到任何章节文件")

    total, short = 0, []
    for n, f in chaps:
        t = lib.read(f)
        h1 = re.findall(r"^#\s+(.+)$", t, re.M)
        if len(h1) != 1: p0.append(f"第{n}章：H1 数量为 {len(h1)}（必须且只能 1 个）")
        m = lib.CHAP_RE.search(h1[0]) if h1 else None
        if not m or int(m.group(1)) != n:
            p0.append(f"第{n}章：文件内标题章号不一致（{h1[0][:24] if h1 else '无标题'}）")
        if not re.search(r"第\s*%03d\s*章" % n, os.path.basename(f)) and \
           not re.search(r"第\s*%d\s*章" % n, os.path.basename(f)):
            p1.append(f"第{n}章：文件名未按 第NNN章-标题.md")
        w = lib.cjk_count(lib.strip_h1(t))
        total += w
        if w < per * 0.6: short.append((n, w))

    fs = lib.foreshadow(root)
    overdue, bad_status = [], []
    for r in fs:
        if r["status"] not in ("未回收", "已回收", "已放弃", "未埋设"): bad_status.append(r["id"])
        if "未回收" in r["status"] and r["plan_ch"] and nums and r["plan_ch"] <= nums[-1]:
            overdue.append(f"{r['id']}（计划第{r['plan_ch']}章回收，已写到第{nums[-1]}章）")
    if overdue: p0.append("伏笔逾期未回收：" + "；".join(overdue))
    if bad_status: p1.append("伏笔状态取值异常：" + ", ".join(bad_status))

    out = os.path.join(root, "成品", f"{os.path.basename(root)}.md")
    if not os.path.isfile(out):
        p1.append("成品未生成（跑 export_novel.py）")
    else:
        inb = len(lib.chapter_files(root))
        got = len(re.findall(r"^##\s+第\d+章", lib.read(out), re.M))
        if got != inb: p0.append(f"成品章节数 {got} ≠ 正文章节数 {inb}（需重新导出）")

    res = {"chapters": len(chaps), "words": total, "avg": total // max(len(chaps), 1),
           "short_chapters": short, "overdue": overdue, "p0": p0, "p1": p1,
           "pass": not p0}
    human = [f"成品自检：{len(chaps)} 章 / {total} 字（均 {res['avg']}），P0 {len(p0)} 项，P1 {len(p1)} 项"]
    human += ["  ✗ P0 " + x for x in p0]
    human += ["  ! P1 " + x for x in p1[:10]]
    if short: human.append("  ! 偏短章节：" + ", ".join(f"第{n}章({w})" for n, w in short))
    human.append("  ✓ 可交付" if res["pass"] else "  → 先清 P0")
    lib.emit(res, a.json, "\n".join(human))
    return 0 if res["pass"] else 1

if __name__ == "__main__":
    sys.exit(main())
