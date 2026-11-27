# 自检清单（必须带计数写入 verification）

## 第 0/1 步：输入与规则
- [ ] 已读取 `/input/case.json` 与 `/input/task.md`，`case_id` 与 `output_contract` 已记录
- [ ] 已打开全部真实材料（正文、模板、`.cls`/`.sty`、`.bib`、图片说明），`sources` 覆盖所用文件与范围
- [ ] 未用文件名或领域标签推断材料内容
- [ ] 规则表（模板、语言、必改点、禁止改动、输出字段）已建立并在每步重读
- [ ] 骨架 `result.json` 已早期落盘，后续增量更新

## 第 2/3 步：源码与"改得对"
- [ ] 主文件/子文件划分与导言区加载顺序已记录，宏包与版本来源已写明
- [ ] 事实、数字、单位、限定词、否定关系与材料一致；无材料外新增事实
- [ ] 公式编号、`\label`/`\ref`、符号与单位正斜体/正体逐项核对
- [ ] 表格数值、列宽、对齐、三线表与浮动体位置逐项核对，无缩放掩盖裁切
- [ ] `\cite` 键与 `.bib` 条目一一对应，参考文献样式与排序一致
- [ ] 模板必填项逐项覆盖，缺失字段标 `[待作者确认]` 并进入 uncertainties

## 第 4 步：编译—定位—回修
- [ ] 使用实际探测到的引擎；完整命令与 stdout/stderr 写入 `compile_log.txt`
- [ ] 每条错误都有 `file:line`、原始报错、根因类别、修复动作与重编译结果
- [ ] 修一条根因后重编译继续查，未在首条错误处停止
- [ ] 交叉引用与参考文献已跑足轮次至收敛，无残留 undefined 或 Rerun 提示
- [ ] 无法安装/修复的项写了 partial 与人工接管位置，未伪造成功日志
- [ ] 计数：已定位根因错误数 / 错误总数

## 第 5 步：带计数的证据与诚实性
- [ ] `verification` 八项均有 `result` 与带计数/片段的 `evidence`
- [ ] `compile_success`：最终轮次 exit code 与日志片段
- [ ] `formula_numbering` / `table_width` / `citation_ref_convergence` / `template_required_fields`：通过项 / 检查项
- [ ] `anchor_spotcheck`：按锚点回查成功数 / 抽查数（记录抽查片段）
- [ ] `no_new_facts`：材料外新增事实数为 0，并写明抽查方式
- [ ] `editable_source`：/app/output 下真实存在的可编辑 `.tex` 路径
- [ ] 缺口、冲突、权限不足写入 uncertainties；回修记入 change_log；status 与实际一致

## 提交前检查
- [ ] `result.json` 原样回填 `case_id` 与全部 `output_contract` 字段
- [ ] `main.tex` / `changes.patch` / `compile_log.txt` / `build_manifest.md` / `evidence_map.md` 均已写盘
- [ ] 包内不含 `result.json`、正式案例答案或预制输出
- [ ] 资源为 UTF-8 文本、相对路径、无符号链接，单文件 ≤500KB、总量 ≤2MB
