#!/usr/bin/env python3
"""单章一次性过全部门禁（A/B 循环用）：字数 + 细纲覆盖 + 钩子 + 重复率。"""
import argparse, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

HERE = os.path.dirname(os.path.abspath(__file__))

def run(tool, *args):
    p = subprocess.run([sys.executable, os.path.join(HERE, tool), *map(str, args), "--json"],
                       capture_output=True, text=True)
    try: data = json.loads(p.stdout[p.stdout.index("{"):])
    except (ValueError, json.JSONDecodeError): data = {"error": (p.stdout + p.stderr)[:400]}
    return p.returncode, data

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--chapter", type=int, required=True)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = a.project.rstrip("/")
    f = dict(lib.chapter_files(root)).get(a.chapter)
    if not f: print(f"找不到第{a.chapter}章正文", file=sys.stderr); return 2

    rc_plan, plan = run("check_chapter_plan.py", "--project", root, "--chapter", a.chapter)
    rc_dup, dup = run("dup_check.py", "--project", root, "--chapter", a.chapter)
    words = lib.cjk_count(lib.strip_h1(lib.read(f)))
    hook = lib.hook_type(lib.read(f))

    gates = {
        "plan": {"pass": rc_plan == 0, "problems": plan.get("problems", []),
                 "missed_points": [m["point"] for m in plan.get("missed", [])]},
        "dup": {"pass": rc_dup == 0, "worst": dup.get("worst", {}),
                "pairs": dup.get("pairs", [])[:3]},
    }
    passed = all(g["pass"] for g in gates.values())
    res = {"chapter": a.chapter, "words": words, "hook": hook, "gates": gates, "pass": passed}
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        L = [f"第{a.chapter}章门禁：{words} 字，钩子={hook} → {'通过' if passed else '未通过'}"]
        L.append(f"  细纲覆盖：{'✓' if gates['plan']['pass'] else '✗ ' + '；'.join(gates['plan']['problems'])}")
        if gates["plan"]["missed_points"]:
            L += [f"    漏点：{p[:28]}" for p in gates["plan"]["missed_points"][:5]]
        L.append(f"  重复率：{'✓' if gates['dup']['pass'] else '✗'} 最高 {gates['dup']['worst'].get('ratio', 0)*100:.1f}%")
        if not passed: L.append("  → 交回写作代理修一轮（最多 2 轮）")
        print("\n".join(L))
    return 0 if passed else 1

if __name__ == "__main__":
    sys.exit(main())
