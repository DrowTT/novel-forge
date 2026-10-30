#!/usr/bin/env python3
"""新建小说项目骨架：小说/<书名>/{设定,大纲/细纲,正文,追踪,审稿,成品}。"""
import argparse, datetime, os, sys

FILES = {
"项目.md": """# {title}

- 书名：{title}
- 题材：{genre}
- 形态：{form}
- 目标字数：{words}
- 单章目标：{chapter_words}
- 目标平台：{platform}
- 日更章数：{daily}
- 当前进度：项目初始化
- 下一交付：总纲
- 创建时间：{today}

## 一句话故事

（主角 + 处境 + 目标 + 阻力 + 代价；写成一句读得通的话，占位()不算数）
""",
"设定/世界观.md": """# 世界观

## 舞台
## 规则（硬约束，不得违背；每条都要能推出情节限制）
1.
2.
3.
## 势力与组织
| 名称 | 目标 | 资源 | 与主角关系 |
|---|---|---|---|
## 场景库
## 日常细节（吃穿住行/货币/技术水位）
""",
"设定/人设.md": """# 人物

## 主角
- 姓名：
- 外在目标：
- 内在缺口：
- 能力与限制：
- 说话习惯（口头禅/句长/忌用词）：

## 主要配角
| 姓名 | 功能位 | 与主角关系 | 自身目标 | 结局走向 |
|---|---|---|---|---|
|  |  |  |  |  |

## 反派/对手
""",
"大纲/00-总纲.md": """# 《{title}》总纲

## 一句话故事
## 核心冲突
## 三幕结构
1. 建置：
2. 对抗：
3. 收束：
## 主线里程碑
1.
2.
3.
## 分卷规划
| 卷 | 章节范围 | 卷目标 | 卷末转折 |
|---|---|---|---|
| 一 | 1-{vol_len} |  |  |
## 结局预设
（终点画面 + 主角最终状态）
""",
"大纲/10-卷纲-卷一.md": """# 卷一 卷纲

- 章节范围：1-{vol_len}
## 本卷目标
## 主要事件链（按章，编号列表；gen_outline.py 会按顺序分配给细纲）
1.
2.
3.
## 本卷新增设定/角色
## 本卷埋设伏笔
""",
"大纲/细纲/.gitkeep": "",
"正文/.gitkeep": "",
"追踪/状态.md": """# 状态追踪

| 章节 | 时间点 | 地点 | 在场人物 | 关键物 | 未结事项 |
|---|---|---|---|---|---|
""",
"追踪/伏笔.md": """# 伏笔台账

<!-- 每行：编号 | 埋设章 | 内容 | 指向 | 计划回收章 | 状态（未回收/已回收/已放弃） -->
| 编号 | 埋设章 | 内容 | 指向 | 计划回收章 | 状态 |
|---|---|---|---|---|---|
""",
"追踪/时间线.md": """# 时间线

| 时间 | 事件 | 章节 | 影响 |
|---|---|---|---|
""",
"追踪/发布.md": """# 发布台账（连载必填）

<!-- 状态：存稿 / 已排期 / 已发布；已发布的章正文只读，问题靠后文补救 -->
| 章号 | 状态 | 发布日期 | 追读率 | 完读率 | 备注 |
|---|---|---|---|---|---|
""",
"审稿/.gitkeep": "",
"CHANGELOG.md": "# CHANGELOG\n\n",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("title")
    ap.add_argument("--genre", default="待定")
    ap.add_argument("--form", default="长篇连载")
    ap.add_argument("--words", default="待定")
    ap.add_argument("--chapter-words", dest="cw", default="2500")
    ap.add_argument("--platform", default="待定")
    ap.add_argument("--daily", default="5")
    ap.add_argument("--vol-len", dest="vl", default="20")
    ap.add_argument("--volumes", type=int, default=1, help="额外生成的卷纲份数")
    ap.add_argument("--root", default="小说")
    a = ap.parse_args()
    base = os.path.join(a.root, a.title)
    if os.path.exists(base):
        print(f"已存在，跳过：{base}"); return 0
    for rel, tpl in FILES.items():
        p = os.path.join(base, rel)
        if rel.endswith(".gitkeep"):
            os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").close(); continue
        os.makedirs(os.path.dirname(p) or base, exist_ok=True)
        open(p, "w", encoding="utf-8").write(tpl.format(
            title=a.title, genre=a.genre, form=a.form, words=a.words,
            chapter_words=a.cw, platform=a.platform, daily=a.daily,
            vol_len=a.vl, today=datetime.date.today().isoformat()))
    for v in range(2, a.volumes + 1):
        s = (v - 1) * int(a.vl) + 1
        tpl = FILES["大纲/10-卷纲-卷一.md"].format(title=a.title, vol_len=a.vl)
        tpl = tpl.replace("卷一 卷纲", f"卷{v} 卷纲").replace(
            f"- 章节范围：1-{a.vl}", f"- 章节范围：{s}-{s + int(a.vl) - 1}")
        open(os.path.join(base, "大纲", f"10-卷纲-卷{v}.md"), "w", encoding="utf-8").write(tpl)
    print("已创建：", base)
    for r, _, fs in os.walk(base):
        for f in sorted(fs):
            print("  ", os.path.relpath(os.path.join(r, f), base))
    return 0

if __name__ == "__main__":
    sys.exit(main())
