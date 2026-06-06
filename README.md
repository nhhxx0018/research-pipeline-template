# Research Pipeline — 个人科研流水线(模板)

> 单文件、无服务器的个人科研工作台:**文献库 + 实验追踪**。
> 数据是可编辑的 JSON / Markdown,跑一个 build 脚本注入进单页 HTML —— 双击即看、能进 git、不依赖任何服务。

![文献库](docs/screenshot-vault.png)
![实验追踪](docs/screenshot-experiments.png)

---

## 这是什么

两块看板 + 一套科研生命周期目录:

- **文献库 (Paper Vault)** —— 把论文沉淀成可检索卡片:按 **阶段 / 主题 / 项目 / 状态** 筛选,带中文摘要、标签、arXiv 链接。
- **实验追踪 (Experiments)** —— 每条实验是一个 Markdown(frontmatter 指标 + 观察 / 想法 / 要读的论文 + 内联图),自动汇成项目时间线;另有一个浏览器本地可编辑的**实验计划看板**。
- **7 阶段目录骨架**:选题 → 文献雷达 → 下载 → 精读 → 实验 → 写作 → 交付,每个阶段挂对应的 skill。

## 为什么这么设计(核心思路)

- **纯文本 + 构建注入,不做 Web app**:数据存 JSON / MD,`build.py` 把它内联进 HTML 里的 `<script type="application/json">` 块。
  → **不用服务器、不用数据库、绕开浏览器对本地文件的 CORS 限制、能进 git diff、十年后还打得开。**
- **单文件 HTML**:每个看板就一个 `.html`,双击打开,纯前端、零依赖。
- 整个使用循环只有一句:**改数据 → 跑脚本 → 刷新网页。**

## 目录结构

```
00-inbox/ … 07-delivery/      7 阶段骨架(选题/雷达/下载/精读/实验/写作/交付)
paper-vault/pipeline.json      文献库 + 阶段 + skill 的数据源
05-experiments/<项目>/         project.md + runs/*.md (+ runs/figures/)
dashboard/
  pipeline.html                文献库看板(单文件)
  experiments.html             实验看板(单文件)
  build.py                     把 pipeline.json 注入 pipeline.html
  build-experiments.py         把 05-experiments/ 注入 experiments.html
```

## 数据流

```
改 paper-vault/pipeline.json        ─► python3 dashboard/build.py             ─► 刷新 pipeline.html
丢一条 05-experiments/<项>/runs/*.md ─► python3 dashboard/build-experiments.py ─► 刷新 experiments.html
```

## 怎么用

**加一篇论文**:在 `pipeline.json` 的 `papers` 里加一个条目(字段照现有 ECoT / DriveLM 示例),跑 `build.py`。

**加一次实验**:在 `05-experiments/<项目>/runs/` 放一个 md:

```markdown
---
project: my-project
run: r1-something
date: 2026-01-01
status: done          # done / running / queued / failed
metrics:
  success_rate: 0.42
  vs_baseline: +0.05
---
## 观察
…
## 下一步想法
…
## 图
![说明](figures/xxx.png)
```

跑 `build-experiments.py`。图片放 `runs/figures/` 会自动**内联显示**(点击看大图)。

> ⚠️ **一个坑**:frontmatter 用的是缩进式解析(非完整 YAML),**别在数值后写行内 `#` 注释** —— 注释会被并进数值里,导致指标变成字符串、status 失效。要写说明就放进正文。

## 依赖

- **Python 3**(标准库即可,**无第三方依赖**)—— 跑两个 build 脚本。
- 看板是纯 HTML,任意浏览器双击打开即可。
- 截图用的 headless Chrome / LibreOffice 都不是必需。

## Skills

`pipeline.json` 里列了 7 个阶段各自推荐挂载的 skill(及其 GitHub 源)。
**本模板不含 skill 代码**(均为第三方),需要时照 json 里的 repo 链接自行安装到 `.claude/skills/`。

## 复用

本模板从一个真实科研项目剥离而来,留了 **ECoT / DriveLM** 两篇示例论文 + **一个示例实验**做格式演示。把示例换成你自己的内容即可。
