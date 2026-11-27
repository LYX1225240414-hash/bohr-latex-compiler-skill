# 字段字典

`output_contract` 中的字段优先：同名时以合同为准，不得改名或遗漏；本表扩展字段补充在合同字段之后。

| 字段 | 类型 | 含义 |
|---|---|---|
| case_id | string | 从 case.json 原样回填；确实没有才填 `N/A` |
| status | string | `success` / `partial` / `unable` / `refused` |
| latex_artifacts | array | `path` / `role` / `editable` / `source_anchor`；路径真实存在于 `/app/output` |
| main_result | object | 可编辑源码摘要、目标模板与主要改动点 |
| compile_diagnosis | object | `passes` / `final_exit_code` / `errors` / `warnings` / `converged` |
| revision_record | array | `round` / `problem` / `fix` / `file_line` / `recompiled` / `result` |
| formula_table_check | array | `item` / `kind` / `intended` / `actual` / `consistent` / `anchor` |
| build_manifest | object | `engine` / `tex_distribution` / `template_version` / `packages` / `fonts` / `commands` / `passes` / `output_files` |
| evidence_map | array | `claim` / `value` / `source_type` / `evidence` / `anchor` / `change_record` |
| verification | object | 每项 `result` + 带计数/片段的 `evidence` |
| uncertainties | array | `item` / `reason` / `anchor` / `question_for_author` |
| sources | array | 输入文件与页码/段号/公式号/表格号/`.tex` 行号 |
| change_log | array | 问题 / 修正 / 位置 / 时间顺序 |

## source_type 允许值
`material` / `template` / `source_tex` / `bib` / `compile_log` / `author_confirmation`；不写"推断""常识"。

## kind 允许值
`equation` / `table` / `ref` / `cite` / `template_field`。

## 锚点格式
`p<页>:<段>` / `<章节>:<段>` / `eq<号>` / `tab<号>` / `fig<号>` / `tex:<文件:行>` / `bib:<键>` / `log:<行号或片段>`。
锚点必须指向真实材料位置或真实编译日志；无法定位的条目写入 uncertainties，不填伪造锚点。

## verification 计数项
- `compile_success`：最终 exit code 与日志证据
- `error_root_cause`：已定位根因错误数 / 错误总数
- `formula_numbering`、`table_width`、`citation_ref_convergence`、`template_required_fields`：通过项 / 检查项
- `anchor_spotcheck`：回查成功数 / 抽查数
- `no_new_facts`：材料外新增事实数（必须为 0）
- `editable_source`：真实可编辑源码路径
