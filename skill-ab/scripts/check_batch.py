#!/usr/bin/env python3
"""批次门禁（S7.4）：连续 5 章的章节功能分布与钩子强度是否单调。"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--last", type=int, default=5)
    ap.add_argument("--run", type=int, default=3, help="连续同型上限")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = a.project.rstrip("/")
    chaps = [n for n, _ in lib.chapter_files(root)][-a.last:]
    seq = []
    for n in chaps:
        o = lib.outline(root, n) or {"fields": {}}
        f = dict(lib.chapter_files(root))[n]
        seq.append({"chapter": n,
                    "func": o["fields"].get("功能", ""),
                    "hook": o["fields"].get("钩子", "") or lib.hook_type(lib.read(f))})
    def runs(key):
        out, i = [], 0
        while i < len(seq):
            j = i
            while j + 1 < len(seq) and seq[j + 1][key] == seq[i][key]: j += 1
            if seq[i][key] and j - i + 1 >= a.run: out.append((seq[i][key], i, j))
            i = j + 1
        return out
    func_runs, hook_runs = runs("func"), runs("hook")
    dist = {}
    for s in seq: dist[s["func"] or "未标"] = dist.get(s["func"] or "未标", 0) + 1
    problems = [f"连续 {e-i+1} 章功能同为「{k}」（第{seq[i]['chapter']}–{seq[e]['chapter']}章）" for k, i, e in func_runs]
    problems += [f"连续 {e-i+1} 章钩子同为「{k}」（第{seq[i]['chapter']}–{seq[e]['chapter']}章）" for k, i, e in hook_runs]
    if len(dist) < 2: problems.append("功能类型单一：整批只有一种章节功能")
    res = {"chapters": chaps, "seq": seq, "func_dist": dist, "problems": problems, "pass": not problems}
    human = [f"批次检查（第{chaps[0] if chaps else '?'}–{chaps[-1] if chaps else '?'}章）：" +
             "，".join(f"{s['chapter']}:{s['func'] or '未标'}/{s['hook'] or '无钩子'}" for s in seq)]
    human += ["  ✗ " + p for p in problems]
    human += ["  ✓ 通过"] if res["pass"] else ["  → 下一章强制换型（功能或钩子至少换一个）"]
    lib.emit(res, a.json, "\n".join(human))
    return 0 if res["pass"] else 1

if __name__ == "__main__":
    sys.exit(main())
