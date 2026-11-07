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
│   └── v2 … v7/
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

### v2 之后

v2 起 Skill 增加了固定模板、字数下限与评分点映射；v5 起附带可执行的校验脚本：

```bash
python skill/v5/scripts/check.py output/v5/generated.md
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

| 版本 | 迭代重点 | 一句话 |
|:---|:---|:---|
| v1 | 从手工经验抽象 | 把手工版的五段结构写成提示词 |
| v2 | 反馈具体可执行 | 加入章节模板、字数下限、评分点映射表 |
| v3 | 反馈可执行化 | 把「写深一点」改成可判定的验收条件 |
| v4 | 教材术语 | 术语表 + 术语纠错规则，禁止「国密版 AES」这类表述 |
| v5 | 自我检查 | `check.py` 自动校验结构、占位符、术语、Mermaid 语法 |
| v6 | 边界情况 | 无 Linux 实验的周、只有 Head First C 的周、重点/参考分级 |
| v7 | 泛化与稳定 | 周次配置化 `weeks.yaml` + 回归测试，一次生成 12 周 |

---

## 七、环境

- Git 2.56+（Windows）
- Python 3.12（v5 起的校验脚本、v1 起的导图渲染脚本）
- 思维导图渲染：Mermaid 11 + 本机 Microsoft Edge 无头模式（离线可用，不依赖 mermaid.ink）
- PDF 导出：LibreOffice Kit（`cli.js convert --input x.md.docx --output x.pdf`）

> 本机未安装 Git/Python 到 PATH 时，使用便携版：`tools/mingit/cmd/git.exe`、
> `C:\Users\31024\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe`。

---

## 八、提交物

1. 仓库链接：`https://github.com/<你的账号>/password-pre-study-skill`（推送后填写）
2. 最终报告 PDF：`report/final-analysis.pdf`
3. 各周作业 Markdown / PDF：`output/v7/`