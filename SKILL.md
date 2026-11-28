---
name: latex-compiler-pro
description: 面向 LaTeX 写作与编译任务的 Agent Skill：从真实论文材料与模板出发，生成可编辑的 .tex 源码，按错误分类定位到文件与行号并逐轮编译修复，校验公式编号、表格列宽、交叉引用、参考文献与模板必填项，输出带证据锚点、编译命令与版本记录的 result.json；当用户要求撰写、改写、校对、迁入模板、修复编译错误或复现 LaTeX 稿件时使用，支持中英文材料与 pdflatex/xelatex/lualatex。
---

# LaTeX 写作与编译：交得出可编译、可回改、可复现的源码

把材料变成**能在指定模板下真正编译通过、能被别人接着改、并能按记录复现**的 LaTeX 产物，而不是一段看起来正确的片段或一份预制答案。本 Skill 锁定题面要求的四件事：**编译得通**、**改得对**、**交得可用**、**复现得了**；并让每一步都有来源锚点与回修记录。

## 何时使用

- 根据科研材料撰写、改写、校对 LaTeX 段落、公式、表格、引用或结构化写作产物。
- 把已有稿件迁入期刊/会议/学位论文模板，补齐模板必填项与文件结构。
- 定位编译错误、警告与交叉引用未解析问题，修到多轮编译收敛。
- 需要交付可编辑源码、编译日志、版本记录和逐条可回查的证据台账。

不适用：无原始材料、要求编造论文数据或评测成绩、只需一句话大纲的场景。

## 运行环境与输出路径（重要）

- 平台把本 Skill 安装到 `/skills/weekly-skill`，并用固定的 3 个案例运行。先读真实输入 `/input/case.json` 与 `/input/task.md`；`case.json` 可能含 `case_id`、`output_contract`、材料路径、模板路径与目标约束。**以实际字段为准，不从题目标签、文件名或示例推断材料内容**。
- 中间文件写在 `/app/work`，不污染输入目录；资源从 `/skills/weekly-skill/resources/` 读取，均为 UTF-8 文本。
- 最终结构化结果写到 `/app/output/result.json`（UTF-8 合法 JSON），**完整原样回填 `output_contract` 的全部字段与 `case_id`**，再补充本 Skill 的扩展字段；合同字段与本表同名时以合同为准。
- 同时写出**可编辑源码** `/app/output/main.tex`（或题目指定的 `.tex` 路径）、`/app/output/changes.patch`（改动记录）、`/app/output/compile_log.txt`（实际编译轮次与错误）、`/app/output/build_manifest.md`（模板、宏包与字体版本、命令与轮次）、`/app/output/evidence_map.md`。若 `output_contract` 指定其他产物路径，以合同为准；有 PDF 预览能力时另存 `/app/output/main.pdf`，但 PDF 不能代替可编辑源码。
- 预算内**尽早写入诚实的部分结果**再增量完善：64 次模型请求、900 秒、单次 16384 tokens；3 个案例由平台安排，参赛者不提供测试案例、白板或正式答案。
- 尽量让可核验操作轨迹覆盖读取、编辑、编译、回查等 **≥30 个真实动作**，不要只抛出一个最终结论；但不得为凑数编造命令或日志。
- 禁止提交预制答案、正式案例答案、假造的编译日志或评测成绩；本 Skill 包内不应含任何 `result.json`。
- 资源限制：最多 50 个 UTF-8 文本文件、单文件 ≤500KB、总计 ≤2MB、无符号链接。

## 输入输出

输入：任务说明与科研材料（文件或路径）、目标模板/类文件、导言区或既有 `.tex`、`.bib`、图片与字体说明；可选约束：目标期刊、语言、编译引擎、禁止改动项。

输出 `result.json` 字段如下（`output_contract` 优先）：

| 字段 | 要求 |
|---|---|
| case_id | 从 case.json 原样回填；确实没有才填 `N/A` |
| status | `success` / `partial` / `unable` / `refused`；部分完成须写明未完成范围与人工接管位置 |
| latex_artifacts | 数组，每项含 `path` / `role`（main/chapter/style/bib/figure/preview）/ `editable` / `source_anchor`；路径为 `/app/output` 下真实存在的文件 |
| main_result | 对象，给出最终可编辑源码的摘要、目标模板与主要改动点；完整正文在 `latex_artifacts` 指向的 `.tex` 中 |
| compile_diagnosis | 对象，含 `passes`、`final_exit_code`、`errors`（每项 `file` / `line` / `message` / `root_cause` / `fix` / `verified`）、`warnings`、`converged`；**不得停在第一条报错** |
| revision_record | 数组，每项 `round` / `problem` / `fix` / `file_line` / `recompiled` / `result` |
| formula_table_check | 数组，每项 `item` / `kind`（equation/table/ref/cite/template_field）/ `intended` / `actual` / `consistent` / `anchor` |
| build_manifest | 对象，含 `engine`、`tex_distribution`、`template_version`、`packages`、`fonts`、`commands`、`passes`、`output_files`；未探明的写 `unknown` 并进 uncertainties，不猜 |
| evidence_map | 数组，每项 `claim` / `value` / `source_type` / `evidence` / `anchor` / `change_record`；数字、术语、公式、引用均可逐条回查 |
| verification | 对象，逐项给 `result`（pass/fail/na）与**带计数或抽查片段**的 `evidence`：`compile_success`、`error_root_cause`、`formula_numbering`、`table_width`、`citation_ref_convergence`、`template_required_fields`、`anchor_spotcheck`、`no_new_facts`、`editable_source` |
| uncertainties | 数组，每项 `item` / `reason` / `anchor` / `question_for_author`；缺宏包、缺字体、模板类缺失、材料冲突、权限不足分别写明 |
| sources | 使用的输入文件与页码/段号/公式号/表格号/`.tex` 行号，界定输入边界 |
| change_log | 自检回修记录：问题、修正、位置、按时间顺序 |

**锚点格式**：`p<页>:<段>`、`<章节>:<段>`、`eq<号>`、`tab<号>`、`fig<号>`、`tex:<文件:行>`、`bib:<键>`、`log:<行号或片段>`，必须指向输入材料或真实编译日志中的位置。

## 工作流

### 第 0 步：落盘骨架（先保底）
读 `/input/case.json` 与 `/input/task.md`，确认 `case_id`、`output_contract`、材料与模板路径；在 `/app/work` 建工作副本，立即向 `/app/output/result.json` 写入 `case_id`、`status: partial`、各字段空数组的骨架，后续逐段增量更新。先写出一份最小可编译骨架 `.tex` 再逐步填充，避免超时只留下空结果。

### 第 1 步：确认输入边界与规则表
打开全部实际材料（论文正文、表格、图片说明、模板、`.cls`/`.sty`、`.bib`），**不靠文件名或领域标签猜内容**；记录 `sources`。从任务说明抽取目标模板、文体、语言、必须改动点、禁止改动项、输出字段，形成规则表并在每步重读。缺文件 → `status: unable` 并写明具体路径；扫描页可尝试 OCR，失败写入 uncertainties。

### 第 2 步：源码结构与宏包规划（交得可用）
按 `resources/latex_playbook.md` 先确定主文件与子文件划分、导言区加载顺序、引擎与模板约束：
- 用模板原有结构与必填项，不重写模板；缺 `.cls`/`.sty` 时记录路径与影响，不用相似模板冒充。
- 宏包按需加载并记录版本来源；避免重复加载与已知冲突（如 `inputenc` 与 XeLaTeX、`hyperref` 加载顺序）。
- 中英文混排、字体和编码随引擎选择；缺字体写 uncertainties，不静默替换导致版式变化。
- 每段正文附来源锚点；事实、数字、单位、限定词、否定关系原样保留，不新增材料外事实。

### 第 3 步：内容改写与"改得对"核对
逐块生成或修改 LaTeX 源码，同时填 `formula_table_check`：
- 公式：多行对齐、编号与 `\label`/`\ref` 一致，符号、上下标、变量正斜体与单位正体符合原文含义。
- 表格：列宽与数值对齐，三线表样式、跨页与浮动体位置合理，不靠整体缩放掩盖溢出；每格数值可回到材料锚点。
- 引用：`\cite` 键与 `.bib` 条目一一对应，正文引用与参考文献表排序/样式一致；`undefined citations` 必须修到收敛。
- 模板：逐项补齐标题、作者、摘要、关键词等必填项，缺失项标 `[待作者确认]` 并写 uncertainties。

### 第 4 步：编译—定位—回修闭环（编译得通）

**先进静态预检，再真编译**。很多编译错误在无 LaTeX 环境时也能静态发现，先扫一遍能把"编译—改—再编译"的轮次压到最少：

```bash
T=/skills/weekly-skill/resources/scripts/tex_lint.py
python3 "$T" check  --tex /app/work/main.tex --bib /app/work/refs.bib --out /app/work
cat /app/work/tex_report.md
```

| 级别 | 典型问题 | 处理 |
|---|---|---|
| error | 环境未闭合/嵌套不匹配、花括号不平衡、缺 `\documentclass`/`\begin{document}`、tabular 列数与 `&` 不符、`\label` 重复、bib 中无此 `\cite` key | 必须全部改到 0 再编译 |
| warning | 行内 `$` 未闭合、`\ref` 无对应 `\label`、特殊字符 `_ # ^` 未转义、含中文但未加载 ctex/xeCJK | 逐条确认：真问题就改，误报就记入 change_log |
| info | 未被引用的 `\label`、`\includegraphics` 路径 | 按需处理 |

`labels` 子命令可单独导出 `\cite`/`\label`/`\ref` 对照表，便于人工核对引用是否收敛：
```bash
python3 "$T" labels --tex /app/work/main.tex --bib /app/work/refs.bib
```

静态通过后，用 `resources/latex_playbook.md` 的错误分类表执行真编译，禁止"看到第一条错误就停下"：
1. 在 `/app/work` 以 `-interaction=nonstopmode -file-line-error` 调用实际引擎（pdflatex/xelatex/lualatex，按模板选择），完整输出写入 `/app/output/compile_log.txt`。
2. 对每条错误记录 `file:line`、原始报错、**根因**与修复动作；按根因分类（宏包缺失、命令未定义、参数失控、文件缺失、字体缺失、引用/编号未收敛、表格溢出、模板冲突、权限）逐条处理，一条修复后可引发后续错误，需重新编译继续查。
3. 交叉引用与参考文献按引擎要求重复 2–3 遍直到 `\ref`/`\cite` 全部解析、`Rerun` 提示消失；把每轮退出码与轮次写入 `compile_diagnosis.passes`。
4. 每次修复更新 `/app/output/changes.patch` 与 `revision_record`，并增量写回 `result.json`。
5. 若环境确实缺宏包/字体/类文件且无法安装，不伪造成功：`status: partial`，保留最小可编译回退源码，写清缺失项与人工接管位置。
6. 若环境完全没有 LaTeX 引擎：**不得伪造编译成功**。写明"环境无引擎"，改为交付静态检查通过的可编译源码，`status: partial`，并在 `compile_diagnosis` 记录 `engine_unavailable`。

### 第 5 步：带计数的自检（复现得了）
逐项核对 `resources/checklist.md`，把**计数**写进 `verification`（静态项优先用 `tex_report.json` 的 `verification_hint`）：
- `compile_success`：最终轮次 exit code 与日志证据；若引擎不可用则写 `na` 并说明；
- `error_root_cause`：已定位根因的错误数 / 错误总数（静态错误应为 0 才进入编译）；
- `formula_numbering` / `table_width` / `citation_ref_convergence` / `template_required_fields`：通过项 / 检查项，附抽查片段；
- `anchor_spotcheck`：按锚点回查成功数 / 抽查数；`no_new_facts`：材料外新增事实数（必须为 0）；`editable_source`：`/app/output` 下真实可编辑 `.tex` 路径。
失败项回到第 3–4 步修正并记入 `change_log`；仍无法解决则保留 `partial`，不得把失败写成通过。

### 第 6 步：交付与复核
写出 `/app/output/result.json` 与全部可编辑产物，确认：`case_id` 已回填、`output_contract` 字段齐全、`latex_artifacts` 中路径真实存在、`build_manifest` 记录引擎/模板/宏包/字体/命令与轮次、`uncertainties` 与 `change_log` 如实填写。最终答复只做简要说明，详细证据留在产物中。

## 异常处理

| 情况 | 处理 |
|---|---|
| 模板 `.cls`/`.sty` 缺失 | 记录期望路径与报错行，不换模板冒充；能降级时给最小骨架并标 partial |
| 缺宏包/字体 | 查镜像已装版本，能安全替代并记录差异；否则写 uncertainties，不伪造安装成功 |
| 报错级联 | 每轮修一条根因后重编译，按 `file:line` 逐条销账，不只看首条错误 |
| 引用/编号未收敛 | 增加编译轮次并核对 `.aux`/`.bbl`，仍有 undefined 则写明具体键与位置 |
| 表格溢出/浮动体错位 | 调列宽、表头与位置约束并复编译，不靠缩放掩盖裁切 |
| 图表为图片或材料冲突 | 保留占位与锚点，并列冲突与各自来源，交作者确认，不猜内容 |
| 权限不足/超时 | 写明失败路径与已完成部分，尽早落盘 partial，不编造编译日志 |

## 资源

- `resources/scripts/tex_lint.py`：**执行内核**。`check` 静态检出环境未闭合、花括号不平衡、`$` 未闭合、缺文档结构、tabular 列数不符、重复 `\label`、悬空 `\cite`/`\ref`、特殊字符未转义、中文缺 ctex；`labels` 导出引用对照表。`--out` 可传目录（写入约定文件名）或直接传文件名，两种写法都不会报错。纯标准库，不需要 LaTeX 发行版。
- `environment/resources.yaml`：资源清单、依赖、引擎选择与产物说明。
- `resources/latex_playbook.md`：编译命令、错误分类 → 根因 → 修复策略、引用收敛与复现清单模板。
- `resources/checklist.md`：带计数的自检清单。
- `resources/field_dict.md`：字段字典、锚点格式与 verification 计数项。
- `resources/output_example.json`：输出结构示意（占位示例，非答案）。
- `examples/README.md`：最小调用示例（示意）。

## 最小示例（示意，非真实案例）

```bash
T=/skills/weekly-skill/resources/scripts/tex_lint.py
python3 "$T" check  --tex /app/work/main.tex --bib /app/work/refs.bib --out /app/work
python3 "$T" labels --tex /app/work/main.tex --bib /app/work/refs.bib
cat /app/work/tex_report.md
```

示意输出（仅结构）：

```json
{"errors": 0, "warnings": 2, "infos": 3, "cites": 24, "labels": 11, "refs": 19, "environments": 9}
```

真正的结果必须来自本次实际运行，示意输出不得冒充正式案例答案。

## 最小示例

见 `examples/README.md`。示意输出仅展示字段结构，不代表任何真实科研案例的源码或评测结果。
