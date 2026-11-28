# 最小调用示例（示意，非正式案例）

本示例仅演示接口与字段结构，不代表任何真实科研案例的 LaTeX 源码、编译日志或评测结果。

## 输入

```json
{
  "case_id": "示意-case-001",
  "task": "根据给定论文片段与模板改写为可编译的 LaTeX 段落，保留公式编号与引用来源",
  "materials": ["paper_excerpt.md", "template.cls", "refs.bib"],
  "output_contract": {"case_id": "string", "status": "string", "latex_artifacts": "array"}
}
```

实际评测时输入为 `/input/case.json` 与 `/input/task.md`，材料路径以其中字段为准。

## 调用

1. 在 Agent 中加载本 Skill（安装位置 `/skills/weekly-skill`）。
2. 先执行 `python3 /skills/weekly-skill/resources/scripts/tex_lint.py init --case /input/case.json --out /app/output` 落盘合同骨架（`status: partial`，空占位不是答案）。
3. 按 SKILL.md 第 0–6 步执行：写最小可编译 `.tex` 到 `/app/output`，再用 `tex_lint.py check` / `labels` 做静态预检，增量完善。
4. 用 `resources/latex_playbook.md` 做编译—定位—回修闭环，用 `resources/checklist.md` 做带计数自检。
5. 输出 `/app/output/result.json`、`main.tex`、`changes.patch`、`compile_log.txt`、`build_manifest.md`、`evidence_map.md`。

## 示意输出

字段结构见 `../resources/output_example.json`；其中所有取值均为占位示例，`status` 为 `partial`，不得当作正式案例答案或评测结果。
