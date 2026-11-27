# LaTeX 编译—定位—回修手册（结构示意，非答案）

本文件是执行时查阅的**策略表**，不含任何正式案例答案。所有命令与版本以实际环境探测结果为准；探测不到就写 `unknown` 与 uncertainties。

## 1. 引擎与编译命令

先由模板/任务确定引擎，再按该引擎构造命令；把实际命令原样写入 `build_manifest.commands` 与 `compile_log.txt`。

| 场景 | 典型引擎 | 命令模板（按实际路径替换） | 轮次 |
|---|---|---|---|
| 英文期刊/会议模板 | pdflatex | `pdflatex -interaction=nonstopmode -file-line-error -halt-on-error main.tex` | 2–3 遍至 `.aux` 收敛 |
| 中文模板 / 系统字体 | xelatex | `xelatex -interaction=nonstopmode -file-line-error main.tex` | 2–3 遍 |
| 需要 Lua 脚本/现代字体特性 | lualatex | `lualatex -interaction=nonstopmode -file-line-error main.tex` | 2–3 遍 |
| 参考文献 | bibtex / biber | `bibtex main` 或 `biber main`（按 `.bib` 与样式选择） | 正文引擎 → 文献引擎 → 正文 ×2 |

- 不要假设机器上有某个引擎或宏包：先探测（`which <engine>`、`kpsewhich <file>`），记录真实结果。
- 保留完整 stdout/stderr 到 `compile_log.txt`，包括退出码；不要只摘取第一行错误。
- 图、表、公式若有 `.aux` 辅助文件，按"源码改动 → 重编译 → 再看日志"推进，不据旧日志判断新状态。

## 2. 错误分类 → 根因 → 修复策略

对每条报错都写 `file` / `line` / `message` / `root_cause` / `fix` / `verified`；一次只修一条根因后重编译，防止级联误判。

| 报错特征 | 根因类别 | 定位方式 | 修复策略 |
|---|---|---|---|
| `LaTeX Error: File 'xxx.sty' not found` | 宏包缺失 | `kpsewhich xxx.sty` + 报错行 | 查镜像已装版本；必要宏包用等价已装宏包并记差异，否则 partial + uncertainties |
| `Undefined control sequence` | 命令未定义/宏包未加载/拼写错 | 报错行与导言区加载顺序 | 补加载宏包或改为模板已有命令；不猜新命令语义 |
| `Runaway argument?` / `Paragraph ended before ... was complete` | 参数缺右花括号或环境未闭合 | 从报错行向前扫描括号与环境栈 | 补齐 `}` 或 `\end{}`，再全篇括号配平检查 |
| `! I can't find file 'xxx'` / `Figure ... not found` | 输入/图片缺失 | 相对路径与工作目录 | 改用 `/app/work` 内的真实相对路径；缺图保留占位并标 uncertainties |
| `Font ... not found` / `Font Warning` | 字体缺失 | 引擎与字体探测结果 | 换已装同族字体并记录版式差异；不得静默替换后声称完全一致 |
| `Citation ... undefined` / `There were undefined citations` | 文献未收敛或 `.bib` 键不匹配 | `.aux` 与 `.bib` 键清单 | 对齐 `\cite{}` 与 bib 键，按引擎跑 bibtex/biber，再重编译至消失 |
| `Reference ... undefined` / `Rerun to get cross-references right` | 交叉引用未收敛 | `\label` 与 `\ref` 清单 | 补 label、修拼写、增加编译轮次至 `.aux` 稳定 |
| `Overfull \hbox` / `hbadness` | 列宽/行宽溢出 | 表格列定义与版式 | 调整列宽、缩写表头、改 floating 位置；不靠 `\resizebox` 掩盖裁切 |
| `Class ... not found` / 模板必填项报错 | 模板类缺失/字段不齐 | 模板路径与必填项清单 | 记录路径与行号；按模板补必填字段，缺失项标 `[待作者确认]` |
| `Permission denied` / 无法写 `.aux` | 权限不足 | 工作目录权限 | 转 `/app/work` 重试；仍失败标 partial，不伪造编译成功 |

## 3. "改得对"的逐项核对

| 对象 | 必须一致的内容 | 证据位置 |
|---|---|---|
| 公式 | 符号、上下标、单位正斜体/正体、编号与 `\label`/`\ref` | 原材料 `eq<号>` + `tex:<文件:行>` |
| 表格 | 每个数值、列标题、对齐、三线表样式、跨页与标题位置 | 原材料 `tab<号>` + `tex:<文件:行>` |
| 引用 | `\cite` 键 ↔ `.bib` 条目、参考文献样式与排序 | `bib:<键>` + `log:<片段>` |
| 模板 | 类文件版本、必填字段、文件结构、字体与宏包约束 | 模板文件行号 + `build_manifest` |
| 事实 | 数字、单位、限定词、否定关系原样保留，不新增材料外事实 | `p<页>:<段>` / `evidence_map` |

## 4. 复现清单模板（写入 build_manifest.md）

```text
引擎与版本：<实际探测输出>
TeX 发行版：<实际探测输出>
模板/类文件：<路径 + 版本标识>
宏包与版本：<名称 + 版本或 unknown>
字体：<名称 + 来源或 unknown>
输入材料：<case.json 中的材料路径与版本>
命令序列：1) ... 2) ... 3) ...
轮次：<实际编译次数，及收敛判据>
输出文件：<main.tex / main.pdf / compile_log.txt / ...>
限制：<无法探明或未完成的项目，逐条列出>
```

## 5. 反模式（会直接丢分）

- 把预览 PDF/截图当作唯一成果，或未保存可编辑 `.tex`。
- 只交一个 `result.json` 而没有真实源码、编译日志与版本记录。
- 用了预制答案或假造编译日志/评测成绩。
- 遇到第一条错误就停，未销账其余错误与级联问题。
- 缺宏包/字体时静默替换，却声称与原模板一致。
- 事实、数值、引用无锚点，或写入材料外新事实。
