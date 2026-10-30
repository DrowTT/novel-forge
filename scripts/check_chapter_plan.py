#!/usr/bin/env python3
"""章节门禁（S5-4）：细纲要点覆盖 + 章末钩子 + 字数区间。代理指标，非文学判断。"""
import argparse, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--chapter", type=int, required=True)
    ap.add_argument("--cover", type=float, default=0.35, help="要点覆盖下限（字二元组重合）")
    ap.add_argument("--tol", type=float, default=0.15, help="字数容差")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = a.project.rstrip("/")
    f = dict(lib.chapter_files(root)).get(a.chapter)
    if not f: print(f"找不到第{a.chapter}章正文", file=sys.stderr); return 2
    text = lib.read(f)
    body = lib.strip_h1(text)
    o = lib.outline(root, a.chapter)
    meta = lib.project_meta(root)
    target = int(o["fields"].get("字数", "0").replace("字", "") or 0) if o else 0
    target = target or int(re.sub(r"\D", "", meta.get("单章目标", "2500")) or 2500)
    words = lib.cjk_count(body)
    hook = lib.hook_type(body)

    res = {"chapter": a.chapter, "words": words, "target": target, "hook": hook,
           "covered": [], "missed": [], "problems": []}
    if not (target * (1 - a.tol) <= words <= target * (1 + a.tol)):
        res["problems"].append(f"字数 {words} 不在 {int(target*(1-a.tol))}–{int(target*(1+a.tol))} 区间")
    if o and o["points"]:
        for p in o["points"]:
            r = lib.overlap(p, body)
            (res["covered"] if r >= a.cover else res["missed"]).append({"point": p, "ratio": round(r, 2)})
        if res["missed"]:
            res["problems"].append(f"{len(res['missed'])}/{len(o['points'])} 个细纲要点没写进正文")
    else:
        res["problems"].append("没有细纲，无法校验推进（先跑 gen_outline.py）")
    if hook == "无":
        res["problems"].append("章末找不到钩子信号（悬念/危机/反转），断章位置可能过软")
    res["pass"] = not res["problems"]
    human = [f"第{a.chapter}章：{words}/{target} 字，钩子={hook}，覆盖 {len(res['covered'])}/{len(res['covered'])+len(res['missed'])}"]
    human += ["  ✗ " + p for p in res["problems"]]
    human += ["  ✓ 通过"] if res["pass"] else ["  → 补齐后再进下一章"]
    lib.emit(res, a.json, "\n".join(human))
    return 0 if res["pass"] else 1

if __name__ == "__main__":
    sys.exit(main())
