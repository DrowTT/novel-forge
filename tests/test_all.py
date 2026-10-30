#!/usr/bin/env python3
"""novel-forge 全量冒烟测试：每个工具都跑正例与反例，断言退出码。"""
import json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = os.path.join(ROOT, "scripts")
sys.path.insert(0, HERE)
import build_fixture

PASS = FAIL = 0
def run(tool, *args):
    p = subprocess.run([sys.executable, os.path.join(TOOLS, tool), *map(str, args)],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✓ {name}")
    else: FAIL += 1; print(f"  ✗ {name}\n      {detail[:400]}")

def main():
    tmp = tempfile.mkdtemp(prefix="nf-test-")
    proj = build_fixture.build(tmp)

    print("[一致性] skill/scripts 与 scripts 同步")
    import hashlib
    def h(fp):
        return hashlib.sha256(open(fp, "rb").read()).hexdigest()
    src = {f: h(os.path.join(ROOT, "scripts", f)) for f in os.listdir(os.path.join(ROOT, "scripts")) if f.endswith(".py")}
    dst_p = os.path.join(ROOT, "skill", "scripts")
    dst = {f: h(os.path.join(dst_p, f)) for f in os.listdir(dst_p) if f.endswith(".py")} if os.path.isdir(dst_p) else {}
    check("脚本副本一致（否则先 make sync）", src == dst, f"src={len(src)} dst={len(dst)}")

    print("[novel-ab] 技能包完整")
    ab = os.path.join(ROOT, "skill-ab")
    sk = open(os.path.join(ab, "SKILL.md"), encoding="utf-8").read()
    check("frontmatter name 与目录一致", sk.startswith("---") and "name: novel-ab" in sk.split("---")[1], sk[:120])
    check("含 A/B 两套提示词模板", "A 写手提示词模板" in sk and "B 审查提示词模板" in sk)
    abscripts = os.path.join(ab, "scripts")
    same = os.path.isdir(abscripts) and all(
        open(os.path.join(abscripts, f), "rb").read() == open(os.path.join(ROOT, "scripts", f), "rb").read()
        for f in os.listdir(os.path.join(ROOT, "scripts")) if f.endswith(".py"))
    check("scripts 与主仓库一致（否则 make sync）", same)

    print("[new_project] 脚手架")
    check("生成 16 个文件", len([f for _, _, fs in os.walk(proj) for f in fs]) >= 15)

    print("[export_novel] 合并成品")
    rc, out = run("export_novel.py", "--project", proj)
    check("导出成功", rc == 0, out)
    book = os.path.join(proj, "成品", "测试书.md")
    check("成品存在且含目录", os.path.isfile(book) and "## 目录" in open(book, encoding="utf-8").read(), out)

    print("[validate_novel] 成品自检")
    rc, out = run("validate_novel.py", "--project", proj, "--json")
    check("干净项目通过 P0", rc == 0, out)

    print("[context_brief] 写前简报")
    rc, out = run("context_brief.py", "--project", proj, "--chapter", "4", "--json")
    b = json.loads(out[out.index("{"):]) if "{" in out else {}
    check("含细纲字段与卷级远景", rc == 0 and b.get("volume") and b.get("milestones"), out)
    check("给了未完稿章号", b.get("chapter") == 4, out)
    rc, out = run("context_brief.py", "--project", proj)
    check("无细纲时明确提示", "gen_outline.py" in out or "细纲" in out, out)

    print("[gen_outline] 批量细纲")
    rc, out = run("gen_outline.py", "--project", proj, "--from", "4", "--to", "6")
    check("生成 3 份", rc == 0 and os.path.isfile(os.path.join(proj, "大纲/细纲/第006章.md")), out)

    print("[check_outline_coverage] 细纲门禁")
    rc, out = run("check_outline_coverage.py", "--project", proj, "--from", "4", "--to", "6")
    check("占位符细纲被判失败", rc == 1, out)
    rc, out = run("check_outline_coverage.py", "--project", proj, "--from", "1", "--to", "3")
    check("已填细纲通过", rc == 0, out)

    print("[check_chapter_plan] 章节门禁")
    rc, out = run("check_chapter_plan.py", "--project", proj, "--chapter", "1")
    check("对齐章节通过", rc == 0, out)
    off = os.path.join(proj, "正文", "第004章-跑题.md")
    open(off, "w", encoding="utf-8").write("# 第004章 跑题\n\n天气很好，大家都很开心，他们吃了面，又喝了汤，然后睡觉。\n")
    rc, out = run("check_chapter_plan.py", "--project", proj, "--chapter", "4")
    check("跑题章节被拦", rc == 1, out)
    os.remove(off)

    print("[gate_all] 一次性全门禁")
    rc, out = run("gate_all.py", "--project", proj, "--chapter", "1")
    check("合格章通过", rc == 0 and "通过" in out, out)
    off2 = os.path.join(proj, "正文", "第005章-注水.md")
    open(off2, "w", encoding="utf-8").write("# 第005章 注水\n\n天亮了，大家起床，吃饭，聊天，笑，然后出门。\n")
    rc, out = run("gate_all.py", "--project", proj, "--chapter", "5")
    check("不合格章被拦", rc == 1, out)
    os.remove(off2)

    print("[dup_check] 重复检测")
    rc, out = run("dup_check.py", "--project", proj, "--chapter", "3")
    check("正常章节通过", rc == 0, out)
    copy = os.path.join(proj, "正文", "第004章-复制.md")
    open(copy, "w", encoding="utf-8").write(open(os.path.join(proj, "正文", "第001章-停电.md"), encoding="utf-8").read())
    rc, out = run("dup_check.py", "--project", proj, "--chapter", "4")
    check("复制章被判重复", rc == 1, out)
    os.remove(copy)

    print("[batch_status] 存稿池")
    rc, out = run("batch_status.py", "--project", proj, "--daily", "2", "--json")
    s = json.loads(out[out.index("{"):]) if "{" in out else {}
    check("buffer=1 → 危险", rc == 0 and s.get("buffer") == 1 and s.get("level") == "危险", out)
    rc, out = run("batch_status.py", "--project", proj, "--daily", "2", "--strict")
    check("strict 在危险期失败", rc == 1, out)

    print("[check_batch] 批次分布")
    for n in (1, 2, 3):
        p = os.path.join(proj, "大纲", "细纲", f"第{n:03d}章.md")
        t = open(p, encoding="utf-8").read().replace("功能: 推进", "功能: 铺垫").replace(
            "功能: 爽点", "功能: 铺垫")
        open(p, "w", encoding="utf-8").write(t)
    rc, out = run("check_batch.py", "--project", proj, "--last", "3")
    check("连续同功能被拦", rc == 1, out)
    p = os.path.join(proj, "大纲", "细纲", "第002章.md")
    open(p, "w", encoding="utf-8").write(open(p, encoding="utf-8").read().replace("功能: 铺垫", "功能: 爽点"))
    rc, out = run("check_batch.py", "--project", proj, "--last", "3")
    check("换型后通过", rc == 0, out)

    print("[checkpoint] 断点记账")
    rc, out = run("checkpoint.py", "--project", proj, "--note", "测试断点")
    log = open(os.path.join(proj, "CHANGELOG.md"), encoding="utf-8").read()
    meta = open(os.path.join(proj, "项目.md"), encoding="utf-8").read()
    check("写了 CHANGELOG 与进度", rc == 0 and "测试断点" in log and "当前进度：已写 3 章" in meta, out)
    check("生成了快照", os.path.isdir(os.path.join(proj, "成品", "snapshots")), out)

    print("[validate_novel] 反例：逾期伏笔 / 跳号 / 成品过期")
    fv = os.path.join(proj, "追踪", "伏笔.md")
    open(fv, "a", encoding="utf-8").write("| F002 | 1 | 老周家门缝 | 邻居变异 | 2 | 未回收 |\n")
    rc, out = run("validate_novel.py", "--project", proj)
    check("逾期伏笔判 P0", rc == 1 and "逾期" in out, out)
    open(fv, "w", encoding="utf-8").write("# 伏笔台账\n\n| 编号 | 埋设章 | 内容 | 指向 | 计划回收章 | 状态 |\n|---|---|---|---|---|---|\n| F001 | 1 | 走廊拖拽声 | 感染源 | 9 | 未回收 |\n")
    os.rename(os.path.join(proj, "正文", "第002章-门缝.md"), os.path.join(proj, "正文", "第007章-门缝.md"))
    rc, out = run("validate_novel.py", "--project", proj)
    check("章号跳号判 P0", rc == 1 and "章号" in out, out)
    os.rename(os.path.join(proj, "正文", "第007章-门缝.md"), os.path.join(proj, "正文", "第002章-门缝.md"))
    rc, out = run("validate_novel.py", "--project", proj)
    check("修复后通过", rc == 0, out)

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n结果：{PASS} 通过 / {FAIL} 失败")
    return 0 if FAIL == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
