# novel-forge

面向 **DeepSeek Harness / 通用 Agent** 的中文长篇小说生产工具链：把"长篇小说怎么写"变成一套可执行、可校验、可断点续跑的流程，而不是每次靠模型即兴发挥。

配套方法论见 [WORKFLOW.md](WORKFLOW.md)（S0–S7 阶段、门禁、断点协议、日更机制）；
不想逐章人工审稿的，用 [docs/AB-LOOP.md](docs/AB-LOOP.md) 的双代理循环（A 写 / B 审 / 脚本硬门禁）。

## 它解决什么

长篇（30 万字以上）或日更连载，真正会崩的从来不是文笔，而是四件事：

| 问题 | 后果 | novel-forge 的做法 |
|---|---|---|
| 上下文遗忘 | 第 12 章和第 3 章设定冲突 | 每章写前注入简报：前文尾部 + 细纲 + 未回收/逾期伏笔 + 硬约束 + 卷级远景 |
| 水文 | 字数够但没推进 | 细纲要点覆盖度校验（字二元组重合）+ 章末钩子检测 |
| 烂尾伏笔 | 埋了不收 | 伏笔台账 + 逾期告警 + 交付前自检 P0 |
| 重复/漂移 | 景物心理段落复用、越写越像总结 | n-gram 重合率检测 + 章节功能分布检查 |

## 安装

```bash
git clone <this-repo> novel-forge && cd novel-forge
make test        # 23 项冒烟测试（正例 + 反例）
make install     # 同步脚本并安装技能到 ~/.dsh/skills/novel-writing
```

`make install` 会把 `skill/` 拷到 `~/.dsh/skills/novel-writing`，DSH 技能目录会自动加载（技能名 `novel-writing`，中文触发词已写进 description）。

只在命令行用也完全可以，技能不是必需的。

## 快速开始

```bash
cd 你的写作工作区
python3 <repo>/scripts/new_project.py "末日余烬" --genre 末世丧尸 --words 80万字 --daily 5

# 1) 填 设定/世界观.md、设定/人设.md、大纲/00-总纲.md、大纲/10-卷纲-卷一.md（这四份是创作决策，模型代笔）
# 2) 出细纲
python3 scripts/gen_outline.py --project 小说/末日余烬 --from 1 --to 10
python3 scripts/check_outline_coverage.py --project 小说/末日余烬 --from 1 --to 10

# 3) 写第一章前的简报
python3 scripts/context_brief.py --project 小说/末日余烬

# 4) 写完一章后过门禁
python3 scripts/check_chapter_plan.py --project 小说/末日余烬 --chapter 1
python3 scripts/dup_check.py        --project 小说/末日余烬 --chapter 1

# 5) 每 5 章记账
python3 scripts/checkpoint.py --project 小说/末日余烬 --note "第1批：开门见尸"

# 6) 日更时看存稿池
python3 scripts/batch_status.py --project 小说/末日余烬 --daily 5

# 7) 交付
python3 scripts/export_novel.py  --project 小说/末日余烬
python3 scripts/validate_novel.py --project 小说/末日余烬
```

## 工具清单

| 脚本 | 阶段 | 作用 | 失败即拦 |
|---|---|---|---|
| `new_project.py` | S0 | 建项目骨架（设定/大纲/细纲/正文/追踪/审稿/成品 + CHANGELOG） | — |
| `gen_outline.py` | S4 | 从卷纲事件链批量生成细纲骨架 | — |
| `check_outline_coverage.py` | S4 | 细纲必填字段、窗口连续性、卷纲事件是否都落到细纲 | ✓ |
| `context_brief.py` | S5-1 | 写前简报：前文尾部、细纲、伏笔（含逾期）、状态、硬约束、卷级远景 | — |
| `check_chapter_plan.py` | S5-4 | 细纲要点覆盖 + 章末钩子 + 字数区间 | ✓ |
| `gate_all.py` | S5-4 | 上两者合并一键跑（A/B 循环用） | ✓ |
| `dup_check.py` | S5-4 | 与前 N 章字符 n-gram 重合率 | ✓ |
| `checkpoint.py` | S5-5 | 更新进度、追加 CHANGELOG、成品快照 | — |
| `batch_status.py` | 日更 | 存稿池余量/欠更/健康度分级 | `--strict` |
| `check_batch.py` | 日更 | 批次内章节功能分布与钩子强度是否单调 | ✓ |
| `export_novel.py` | S7 | 合并成品 md（标题页 + 目录带字数 + 正文） | — |
| `validate_novel.py` | S7 | 章号连续、标题一致、字数分布、伏笔逾期、成品同步 | ✓ |

约定：`--json` 输出机器可读；退出码 `0` 通过、`1` 未通过、`2` 输入错误。

## 项目文件契约

```
小说/<书名>/
├── 项目.md                # 书名/题材/字数/日更章数/进度/下一交付
├── 设定/{世界观,人设}.md
├── 大纲/{00-总纲,10-卷纲-卷N}.md + 细纲/第NNN章.md
├── 正文/第NNN章-标题.md    # 一章一文件
├── 追踪/{状态,伏笔,时间线,发布}.md
├── 审稿/卷N-审稿.md
├── 成品/<书名>.md + 成品/snapshots/
└── CHANGELOG.md
```

兼容 `chinese-novelist` 的扁平布局（`00-人物档案.md` / `01-大纲.md` / `第NNN章-标题.md` 平铺），但同一本书只用一种。

## 设计原则

1. **创作决策不自动化**：题材、人设、卷目标、细纲内容、结局，永远由作者或模型当场判断——脚本只做记账与核对，不做审美判断。
2. **代理指标要明说**：`check_chapter_plan.py` 用二元组重合判断"有没有写进要点"，是代理指标，不是文学评价；它只能拦住水文，不能保证好看。
3. **滚动规划**：细纲只排 5–10 章（日更 10–15 章），写完一个窗口再排下一个。
4. **状态先于文采**：与 `设定/`、`追踪/` 冲突时改句子，不改设定。

## 已知边界

- 只出 Markdown；docx/EPUB 需要 pandoc，未内置。
- 工具是启发式门禁：故意写得"推进但文采差"能过，写得"好但不按细纲"会被拦——按需调 `--cover` / `--threshold`。
- 不做 AI 味改写与多视角审稿；那部分是 `story-review` / `story-deslop` 等技能的职责。

## 许可

MIT。第三方写作方法论（oh-story、chinese-novelist、my-novel）仅作参考，未复制其代码。
