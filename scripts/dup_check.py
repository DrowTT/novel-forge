#!/usr/bin/env python3
"""重复/注水检测：新章与前 N 章的字符 n-gram 重合率。"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--chapter", type=int, required=True)
    ap.add_argument("--window", type=int, default=10, help="与前多少章比较")
    ap.add_argument("--n", type=int, default=8, help="n-gram 长度")
    ap.add_argument("--threshold", type=float, default=0.06, help="单章重合率上限")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = a.project.rstrip("/")
    chaps = lib.chapter_files(root)
    cur = dict(chaps).get(a.chapter)
    if not cur: print(f"找不到第{a.chapter}章", file=sys.stderr); return 2
    mine = lib.shingles(lib.read(cur), a.n)
    rows, worst = [], (None, 0.0)
    for num, f in chaps:
        if num == a.chapter or num < a.chapter - a.window: continue
        other = lib.shingles(lib.read(f), a.n)
        r = len(mine & other) / max(len(mine), 1)
        rows.append({"chapter": num, "ratio": round(r, 3)})
        if r > worst[1]: worst = (num, r)
    res = {"chapter": a.chapter, "n": a.n, "threshold": a.threshold,
           "shingles": len(mine), "pairs": sorted(rows, key=lambda x: -x["ratio"])[:5],
           "worst": {"chapter": worst[0], "ratio": round(worst[1], 3)},
           "pass": worst[1] <= a.threshold}
    human = [f"第{a.chapter}章 vs 前 {len(rows)} 章：最高重合 {res['worst']['ratio']*100:.1f}%"
             f"（第{res['worst']['chapter']}章），阈值 {a.threshold*100:.0f}%"]
    if not res["pass"]:
        human.append("  ✗ 与旧章重合偏高，检查是否复用了景物/心理段落")
        human += [f"    第{p['chapter']}章 {p['ratio']*100:.1f}%" for p in res["pairs"][:3]]
    else:
        human.append("  ✓ 通过")
    lib.emit(res, a.json, "\n".join(human))
    return 0 if res["pass"] else 1

if __name__ == "__main__":
    sys.exit(main())
