#!/usr/bin/env python3
"""存稿池状态（S7.2）：buffer 余量、欠更、已发布冻结清单。"""
import argparse, datetime, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

LEVELS = [(10, "健康", "正常节奏，可改稿与优化"),
          (5, "警戒", "停止回改，优先产能"),
          (1, "危险", "只写不审，S6 推迟"),
          (0, "断更", "应急：回顾章/番外/缩章，同时补 buffer")]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--daily", type=int, default=5, help="日更章数")
    ap.add_argument("--today", default=None, help="YYYY-MM-DD，默认今天")
    ap.add_argument("--strict", action="store_true", help="危险/断更时返回非零")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = a.project.rstrip("/")
    rows = lib.release(root)
    done = [n for n, _ in lib.chapter_files(root)]
    stock = [r["num"] for r in rows if "存稿" in r["status"]]
    sched = [r["num"] for r in rows if "已排期" in r["status"]]
    pub = [r["num"] for r in rows if "已发布" in r["status"]]
    buffer = sorted(set(stock) | set(sched))
    unrecorded = [n for n in done if n not in stock and n not in sched and n not in pub]
    level, act = next((l, t) for lim, l, t in LEVELS if len(buffer) >= lim)
    today = datetime.date.fromisoformat(a.today) if a.today else datetime.date.today()
    last = max([r["date"] for r in rows if r["date"] and "已发布" in r["status"]], default="")
    days = None
    if last:
        try: days = (today - datetime.date.fromisoformat(last)).days
        except ValueError: days = None
    backlog = max(0, (days or 0) * a.daily - len(pub)) if days is not None else 0
    res = {"daily": a.daily, "buffer": len(buffer), "level": level, "action": act,
           "stock": stock, "scheduled": sched, "published": len(pub),
           "unrecorded": unrecorded, "days_since_publish": days, "backlog": backlog,
           "days_of_buffer": round(len(buffer) / a.daily, 1)}
    human = [f"存稿池：{len(buffer)} 章（≈{res['days_of_buffer']} 天@{a.daily}章/天）→ {level}",
             f"  动作：{act}",
             f"  存稿 {len(stock)} / 已排期 {len(sched)} / 已发布 {len(pub)}"]
    if days is not None: human.append(f"  距上次发布 {days} 天，估算欠更 {backlog} 章")
    if unrecorded: human.append(f"  ⚠ 有 {len(unrecorded)} 章正文未登记发布状态：{unrecorded[:8]}")
    lib.emit(res, a.json, "\n".join(human))
    if a.strict and level in ("危险", "断更"): return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
