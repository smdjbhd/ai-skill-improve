# 预习作业 Skill 迭代开发

> 课程：《密码系统设计》
> 作者：20241409 司马平珏
> 目标：把「每周预习报告」这一重复性写作任务，从**手工完成**逐步抽象为一个**可复用的 Skill**，并用 7 轮真实迭代记录它的进化过程。

本仓库同时是作业提交物（Phase 0–10）和 Skill 的工作台：每一版 Skill 都能独立运行，每一版输出都保留了「AI 原始生成」与「人工审阅修改」两份，便于对比。

---

## 一、这个 Skill 解决什么问题

《密码系统设计》每周预习报告有固定骨架（AI 总结 / 反思补充 / 思维导图 / 苏格拉底式学习 / 问题与解决），但每一周要读的章节不同，手工写一份要 2–3 小时，且容易漏评分点。把骨架、教材术语约束、自检规则固化进 Skill 后：

- **输入**：本周学习内容（教材章节、重点小节、配套书目）+ 我实际动手做了什么
- **输出**：符合评分点、可直接提交的 Markdown 预习报告
- **保证**：不编造实验输出、术语准确、思维导图可渲染、每节都有评分点对应内容

---

## 二、目录结构

```
预习作业-skill迭代/
├── README.md                     # 本文件
├── handmade/                     # Phase 1：纯手工完成的第 1 次预习作业
│   ├── homework1.md              # 手写正文（骨架 + 待填正文）
│   ├── reflection.md             # 手写思路、卡壳点、想「要是 AI 能帮我…」的地方
│   └── mindmap.png               # 手写版思维导图截图（交作业前生成）
├── skill/                        # Skill 进化史：v1 → v7
│   ├── v1/
│   │   ├── skill.md              # Skill 本体
│   │   └── changelog.md          # 本版设计思路与改动原因
│   ├── v2 … v6/                  # 同上，逐版加厚
│   └── v7/                       # 配置化版本（也是现在能用的那一版）
│       ├── skill.md              # Skill 本体（课程表驱动）
│       ├── changelog.md
│       ├── weeks.yaml            # 12 周课程表：章节 / 档位 / 有无终端实验 / 三套 profile
│       ├── material/w01.md, w09.md   # 本周素材（听课笔记 + 真实日志引用），缺了就不生成
│       ├── fixtures/w04-graded.md    # 第 4 周分级夹具（占位正文，只验 C19）
│       └── scripts/
│           ├── course.py         # 解析 weeks.yaml，按周算形态/分级/算法表
│           ├── generate.py       # 只产骨架；素材不足退出码 2
│           └── check.py          # 21 项验收，--self-test / --coverage
├── output/                       # 各版 Skill 生成的作业
│   ├── v1/
│   │   ├── generated.md          # AI 原始生成
│   │   ├── human-edited.md       # 人工审阅修改版（含 [批注] 修改原因）
│   │   └── mindmap.png           # 思维导图渲染截图
│   └── v2 … v7/
├── feedback/                     # 每轮给 AI 的反馈记录
│   ├── v1-to-v2.md
│   └── …
├── report/
│   ├── roadmap.md                # 7 轮迭代规划（每轮要解决什么问题）
│   └── final-analysis.md         # Phase 10 总结报告
├── docs/
│   ├── 素材包-第一周.md           # 手写第 1 周时自己整理的概念/命令/坑
│   └── 评分点对照.md              # 逐条对照作业评分表自检
└── tools/
    ├── mermaid.min.js            # 本地 Mermaid 11，离线渲染用
    └── render_mermaid.py         # 提取 ```mermaid 块 → 无头 Edge 渲染 PNG
```

---

## 三、如何运行 Skill

### v1（纯提示词版）

1. 打开 `skill/v1/skill.md`；
2. 把「本周输入」段落替换成本周教材章节与重点；
3. 整段投喂给 AI（Kimi / DeepSeek / ChatGPT 均可），得到 `generated.md`；
4. 人工审阅后写入 `output/vN/human-edited.md`，批注格式见下。

### v7（现在推荐用这一版）

```bash
# 1) 生成骨架（缺素材会报"第 N 周素材不足"并以退出码 2 结束，不会瞎编）
python skill/v7/scripts/generate.py --week 1 --out output/w01.md

# 2) 按素材把正文写满，然后校验（21 项，给文件名:行号）
python skill/v7/scripts/check.py --report output/w01.md --week 1

# 3) 12 周回归：看哪几周能生成、哪几周缺素材
python skill/v7/scripts/generate.py --all --dir tmp/regress

# 4) 检查器自证：好样本必须全绿，4 个人为变异必须被指定规则抓住
python skill/v7/scripts/check.py --self-test

# 5) 规则表与实现是否一一对应
python skill/v7/scripts/check.py --coverage
```

### v5 / v6（保留作对比）

```bash
python skill/v5/scripts/check.py --report output/v5/generated.md --profile crypto
python skill/v6/scripts/check.py --report output/v6/generated.md --profile c-only
```

### 思维导图渲染

`output/vN/mindmap.png` 由报告里的 Mermaid 代码渲染得到。渲染脚本是仓库级工具（各版共用，随提交演进），不依赖在线服务——脚本内部用无头 Edge 加载本地 `mermaid.min.js`：

```bash
python tools/render_mermaid.py output/vN/human-edited.md output/vN/mindmap.png
```

脚本会：提取第一个 ` ```mermaid ` 块 → 生成本地 HTML → 无头 Edge 截图 → Pillow 裁白边。

---

## 四、人工审阅批注规范

`human-edited.md` 中所有人工改动都必须留下痕迹，格式统一为：

```markdown
> [批注] 改动原因：AI 把 SM4 分组长度写成 64 bit，实际为 128 bit；已改，并补了一句分组长度对模式选择的影响。
```

- `[批注]` 只标注**为什么改**，不写「已修改」这类无信息量的话；
- 事实性错误、术语错误、编造的命令输出，必须单独标注；
- 每轮至少 3 条有信息量的批注（v5 之后由自检脚本先筛一遍，人工只处理脚本报不出的语义问题）。

---

## 五、评分点对照

| 阶段 | 要求 | 本仓库对应 |
|:---|:---|:---|
| Phase 0 | Git 仓库 + 目录结构 | 本文件 + 全部目录，commit `[phase0]` |
| Phase 1 | 手工完成第 1 次预习作业 | `handmade/`，tag `phase1-handmade` |
| Phase 2 | 编写初始 Skill | `skill/v1/`，tag `skill-v1` |
| Phase 3–9 | 7 次迭代 | `skill/v2..v7` + `output/v2..v7` + `feedback/`，tag `skill-v2..v7` |
| Phase 10 | 总结报告 | `report/final-analysis.md`，tag `final-report` |

逐条自检见 `docs/评分点对照.md`。

---

## 六、迭代路线（详见 `report/roadmap.md`）

| 版本 | 迭代重点 | 一句话 | 状态 |
|:---|:---|:---|:---|
| v1 | 从手工经验抽象 | 把手工版的五段结构写成提示词 | ✅ 已提交 `skill-v1` |
| v2 | 反馈具体可执行 | 加入章节模板、字数下限、评分点映射表 | ✅ 已提交 `skill-v2` |
| v3 | 反馈可执行化 | 把「写深一点」改成可判定的验收条件（C1–C12） | ✅ 已提交 `skill-v3` |
| v4 | 教材术语 | 术语表 + 术语唯一 + 数值三件套（C13–C18） | ✅ 已提交 `skill-v4` |
| v5 | 自我检查 | `scripts/check.py` 19 项 + `--self-test` + `--coverage` | ✅ 已提交 `skill-v5` |
| v6 | 边界情况 | 三套周形态、三态结果（PASS/FAIL/N/A）、重点/了解/参考分级（C19） | ✅ 已提交 `skill-v6` |
| v7 | 泛化与稳定 | 课程表驱动 `weeks.yaml` + `generate.py` + 12 周回归 | ✅ 已提交 `skill-v7` |

各版的自动校验结果（均为逐项全过）：

| 版本 | 校验脚本 | 断言数 | 结果 | 导图尺寸 |
|:---|:---|:---|:---|:---|
| v1 | 无（人工通读） | — | 5 条批注 / 3 处事实错 | 4626×2381 |
| v2 | 无 | — | 4 条批注 | 4578×3403 |
| v3 | `tmp/check_v3.py`（仓库外） | 20 | 20/20 PASS | 4578×3463 |
| v4 | `tmp/check_v4.py`（仓库外） | 28 | 28/28 PASS | 4592×3106 |
| v5 | `skill/v5/scripts/check.py` | 19 | 19/19 PASS | 4592×3106 |
| v6 | `skill/v6/scripts/check.py`（第 9 周，`c-only`） | 21 | 0 失败 / 5 项 N/A | 4560×2587 |
| v7 | `skill/v7/scripts/check.py --week 1` | 21 | 0 失败 / 0 项 N/A | 4592×3106 |

> v3/v4 的检查器各写一次放在工作区 `tmp/` 里，不通用——这正是 `feedback/v4-to-v5.md` 要求 v5 解决的问题；
> v5 把检查器搬进仓库，v6 让它认周形态，v7 让周形态从 `weeks.yaml` 来。
> 12 周回归现状：`generate.py --all` = 「能生成 2 周，素材不足 10 周」——素材没写就是没写，脚本不会编。

---

## 七、环境

- Git 2.56+（Windows）
- Python 3.12（v5 起的校验脚本、v1 起的导图渲染脚本；只依赖标准库，**不需要 pip install**）
- 思维导图渲染：Mermaid 11 + 本机 Microsoft Edge 无头模式（离线可用，不依赖 mermaid.ink）
- PDF 导出：LibreOffice Kit（`cli.js convert --input x.md.docx --output x.pdf`）

> 本机未安装 Git/Python 到 PATH 时，使用便携版：`tools/mingit/cmd/git.exe`、
> `C:\Users\31024\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe`。

---

## 八、提交物

1. 仓库链接：`https://github.com/<你的账号>/password-pre-study-skill`（推送后填写）
2. 最终报告 PDF：`report/final-analysis.pdf`
3. 各周作业 Markdown / PDF：`output/v7/`

## 九、十二周交付状态

课程表见 `skill/v7/weeks.yaml`（12 周、各章分级、周形态）。当前进度：

| 周 | 主题 | 状态 | 文件 | 还缺什么 |
|---|---|---|---|---|
| 1 | 密码学基础与 Linux 加密环境 | v1–v7 全套，v7 稿 21/21 通过 | `output/v7/generated.md`、`human-edited.md`、`mindmap.png` | **手写正文**（`handmade/homework1.md`）与手绘导图截图 |
| 2 | 指针、结构体与分组密码 | 仅课程表 | — | 素材（读了什么、卡在哪） |
| 3 | 文件与随机数 | 仅课程表 | — | 素材 |
| 4 | 进程与 PKI（三档分级：14 重 / 6 了解 / 8、13 参考） | 仅课程表 + `fixtures/w04-graded.md` | `skill/v7/fixtures/` | 素材；这是唯一能真正验三档分级的周 |
| 5 | 哈希与消息认证 | 仅课程表 | — | 素材 |
| 6 | CSP 与 CryptoAPI | 已生成，19/21 通过 | `output/v7/w06.md`、`w06-mindmap.png` | §5 需有"我答不上来"的轮次；§6 需命令行排查记录 |
| 7 | 身份认证与 PKI | **仅素材** | `skill/v7/material/w07.md`、`handmade/旧稿/` | 真实实验（`openssl ca` 三处）、重跑 PFX 两方向 |
| 8 | SSL/TLS 编程 | **仅素材** | `skill/v7/material/w08.md`、`handmade/旧稿/` | 真实实验（证书验证错误码 20 的复现） |
| 9 | 进程与系统调用 | 已生成，21/21 通过 | `output/v7/w09.md` | 素材可再补真实日志 |
| 10–12 | 进程间通信 / 网络编程 / 多线程 | 仅课程表 | — | 素材 |

第 7、8 周旧稿已归档 `handmade/旧稿/`，两份**都是 AI 生成、本人未加工**，只作素材与反例，不作证据。
两稿在 `check.py` 下均为 21 项失败 12 项（缺七节结构、术语表、分级标记、对话表、四段式问题、可核对的出处）。

只剩三类活必须本人做（见 `docs/评分点对照.md` 第四节）：
1. **第一周手写正文** —— 打完 tag `phase1-handmade` 才算 Phase 1 完成；
2. **真实素材** —— 每读一章，给 15–20 行笔记（讲了什么、哪里没懂、跑了什么、报错原文）；
3. **判断与批注** —— 生成稿的 `human-edited.md` 里那几条 `> [批注]`，得是本人不同意的意见。
