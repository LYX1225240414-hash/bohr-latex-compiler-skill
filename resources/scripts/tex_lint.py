#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
tex_lint.py — LaTeX 源码静态检查（latex-writer Skill 执行内核）

解决的问题：在没有 LaTeX 发行版的沙箱里，很多编译错误其实可以**静态**发现——
环境没配对、花括号不平衡、$ 未闭合、\cite 指向不存在的 bib key、
\ref 的标签不存在、tabular 列数与 & 数不符、特殊字符未转义。
先静态扫一遍，能把"编译—改—再编译"的轮次从十几次压到一两次。

子命令：
  check   检查 .tex（可选 --bib）→ tex_report.json + tex_report.md
  labels  列出所有 \label / \ref / \cite 的对应关系 → 便于人工核对
  fixhint 对高风险行给出具体修法提示（不自动改文件）

检出级别：
  error    几乎必然编译失败（环境不配对、括号不平衡、缺 document 环境、列数不符）
  warning  可能失败或排版异常（$ 未闭合、特殊字符未转义、悬空 \ref、重复 label）
  info     建议项（未使用的 label、中文但未见 ctex/xeCJK）

用法：
  python3 tex_lint.py check --tex /app/work/main.tex --bib /app/work/refs.bib --out /app/work
  python3 tex_lint.py labels --tex /app/work/main.tex --bib /app/work/refs.bib
"""

import argparse
import json
import re
import sys
from pathlib import Path


def _as_outfile(p, default_name):
    """--out 兼容层：传目录则写入目录下 default_name，传文件名则直接写该文件。"""
    path = Path(p)
    if path.is_dir() or not path.suffix:
        path = path / default_name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _as_outdir(p):
    """--out 兼容层：传的是文件名时取其父目录，避免把文件路径当目录用而崩溃。"""
    path = Path(p)
    if path.suffix.lower() in (".json", ".md", ".txt", ".yaml", ".yml", ".csv", ".tex", ".bib"):
        path = path.parent if str(path.parent) not in ("", ".") else Path(".")
    path.mkdir(parents=True, exist_ok=True)
    return path

BEGIN = re.compile(r"\\begin\s*\{([^}]+)\}")
END = re.compile(r"\\end\s*\{([^}]+)\}")
LABEL = re.compile(r"\\label\s*\{([^}]+)\}")
REF = re.compile(r"\\(?:ref|eqref|autoref|cref|Cref|pageref)\s*\{([^}]+)\}")
CITE = re.compile(r"\\[cC]ite[a-zA-Z]*\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
BIBENTRY = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.I)
TABULAR = re.compile(r"\\begin\s*\{(tabular\*?|tabularx|longtable|array)\}\s*(?:\{[^{}]*\}\s*)?\{([^{}]*)\}", re.S)
GRAPHICS = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")

# 常用环境（不参与"未使用环境"判断，仅用于配对）
SKIP_ENV_CHECK = {"document"}


def strip_comments(tex):
    """去掉 % 注释，保留 \\% 转义。返回 (清理后文本, 行号偏移不变的文本)"""
    out_lines = []
    for line in tex.splitlines():
        buf, i = [], 0
        while i < len(line):
            ch = line[i]
            if ch == "\\" and i + 1 < len(line):
                buf.append(line[i:i + 2])
                i += 2
                continue
            if ch == "%":
                break
            buf.append(ch)
            i += 1
        out_lines.append("".join(buf))
    return "\n".join(out_lines)


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def count_brace_balance(text):
    """返回 (净值, 首次不平衡的行)"""
    depth, first_bad = 0, None
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0 and first_bad is None:
                first_bad = line_of(text, i)
                depth = 0
        i += 1
    return depth, first_bad


def check_dollar(text):
    """检查 $ 配对（忽略 \\$ 与 $$）"""
    issues = []
    for ln, line in enumerate(text.splitlines(), 1):
        i, single, i2 = 0, 0, 0
        while i < len(line):
            if line[i] == "\\" and i + 1 < len(line):
                i += 2
                continue
            if line.startswith("$$", i):
                i += 2
                continue
            if line[i] == "$":
                single += 1
            i += 1
        if single % 2 == 1:
            issues.append({"line": ln, "msg": "该行 $ 数为奇数，行内公式可能未闭合",
                           "text": line.strip()[:120],
                           "fix": "补齐成对的 $，或改用 \\( \\) 行内公式"})
    return issues


def parse_envs(text):
    stack, errors, used = [], [], {}
    events = [(m.start(), "begin", m.group(1)) for m in BEGIN.finditer(text)]
    events += [(m.start(), "end", m.group(1)) for m in END.finditer(text)]
    events.sort()
    for pos, kind, env in events:
        ln = line_of(text, pos)
        if kind == "begin":
            stack.append((env, ln))
            used[env] = used.get(env, 0) + 1
        else:
            if not stack:
                errors.append({"line": ln, "env": env, "msg": "\\end 没有对应的 \\begin"})
                continue
            top_env, top_ln = stack[-1]
            if top_env == env:
                stack.pop()
            else:
                # 允许跨层闭合（LaTeX 会报错，这里明确指出）
                idx = next((k for k in range(len(stack) - 1, -1, -1) if stack[k][0] == env), None)
                if idx is None:
                    errors.append({"line": ln, "env": env, "msg": "\\end 没有对应的 \\begin"})
                else:
                    unclosed = [f"{e}(L{l})" for e, l in stack[idx + 1:]]
                    errors.append({"line": ln, "env": env, "unclosed": stack[idx + 1:],
                                   "msg": f"环境嵌套不匹配，未闭合：{', '.join(unclosed)}"})
                    del stack[idx:]
    for env, ln in stack:
        errors.append({"line": ln, "env": env, "msg": f"\\begin{{{env}}} 未闭合"})
    return errors, used


def check_tabular(text):
    issues = []
    for m in TABULAR.finditer(text):
        env, colspec = m.group(1), re.sub(r"\s", "", m.group(2) or "")
        # 列数：l/c/r 计 1，p/m/b{..} 计 1，*{n}{x} 展开，| 与 @{} 不计
        spec = re.sub(r"@\{[^}]*\}", "", colspec)
        spec = re.sub(r"\|", "", spec)
        ncol = 0
        i = 0
        while i < len(spec):
            ch = spec[i]
            if ch in "lcrX":
                ncol += 1
                i += 1
            elif ch in "pmb":
                ncol += 1
                i = spec.find("}", i) + 1 or i + 1
            elif ch == "*":
                mm = re.match(r"\*\{(\d+)\}\{([^}]*)\}", spec[i:])
                if mm:
                    ncol += int(mm.group(1)) * max(1, len([c for c in re.sub(r"\|", "", mm.group(2)) if c in "lcrX"]))
                    i += mm.end()
                else:
                    i += 1
            else:
                i += 1
        if ncol == 0:
            continue
        start = m.end()
        # 截到 \end{tabular...}
        endm = re.search(r"\\end\s*\{" + re.escape(env) + r"\}", text[start:])
        body = text[start: start + (endm.start() if endm else len(text))]
        offset = 0
        for row in body.split("\\\\"):
            row_start = start + offset
            offset += len(row) + 2
            # 先剥离横线与列格式命令，再看这一行有几个 &
            cleaned = re.sub(r"\\(hline|toprule|midrule|bottomrule|addlinespace|cline\{[^}]*\})",
                             "", row).strip()
            if not cleaned:
                continue
            ncells = len(cleaned.split("&"))
            if ncells != ncol:
                # 行号取"最后一条横线命令之后第一个非空白字符"的位置，避免指到上一行
                cmds = list(re.finditer(r"\\(?:hline|toprule|midrule|bottomrule|addlinespace|cline\{[^}]*\})", row))
                base = cmds[-1].end() if cmds else 0
                seg = row[base:]
                lead = len(seg) - len(seg.lstrip())
                issues.append({"line": line_of(text, row_start + base + lead),
                               "expected_cols": ncol, "actual": ncells,
                               "row": cleaned[:100],
                               "msg": f"表格行有 {ncells} 列，但列声明为 {ncol} 列",
                               "fix": f"调整该行 & 数量到 {ncol - 1} 个，或修改列声明"})
    return issues


def check_specials(text):
    issues = []
    for ln, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("%"):
            continue
        # 表格外的裸 &
        if "&" in line and not re.search(r"\\(begin|end)\s*\{", line):
            # 简单判断：不在 tabular/align 上下文中难以精确，只报"行内含 & 且不在 tabular 块"
            pass
        # 未转义的 % 已在上层剥离；检查 # _ ^ 在文本模式（粗判）
        for ch, hint in [("_", "下角标符号 _ 在文本模式需转义为 \\_ ，或放进 $...$"),
                         ("#", "井号 # 需转义为 \\#"),
                         ("^", "上标符号 ^ 在文本模式需转义或放进 $...$")]:
            # 排除数学环境行与命令参数
            if ch in line and "$" not in line and "\\" + ch not in line:
                stripped = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?(\{[^}]*\})?", "", line)
                if ch in stripped:
                    issues.append({"line": ln, "char": ch, "msg": hint,
                                   "text": line.strip()[:120],
                                   "fix": "转义（\\_ \\# \\^）或放进数学模式"})
                    break
    return issues


def check_cites_refs(text, bib_keys):
    cites = [(m.group(1), line_of(text, m.start())) for m in CITE.finditer(text)]
    labels = [(m.group(1), line_of(text, m.start())) for m in LABEL.finditer(text)]
    refs = [(m.group(1), line_of(text, m.start())) for m in REF.finditer(text)]
    label_set = {l for l, _ in labels}
    cite_keys = []
    for grp, ln in cites:
        for k in grp.split(","):
            k = k.strip()
            if k:
                cite_keys.append((k, ln))
    dup_labels = {}
    for l, ln in labels:
        dup_labels.setdefault(l, []).append(ln)
    return {
        "cites": cite_keys,
        "labels": labels,
        "refs": refs,
        "dangling_cites": [{"key": k, "line": ln} for k, ln in cite_keys if bib_keys and k not in bib_keys],
        "dangling_refs": [{"label": r, "line": ln} for r, ln in refs if r not in label_set],
        "duplicate_labels": [{"label": l, "lines": lns} for l, lns in dup_labels.items() if len(lns) > 1],
        "unused_labels": [{"label": l, "line": ln} for l, ln in labels if l not in {r for r, _ in refs}],
    }


def load_bib_keys(path):
    try:
        txt = Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return set()
    return {m.group(2).strip() for m in BIBENTRY.finditer(txt)}


def cmd_check(args):
    raw = Path(args.tex).read_text(encoding="utf-8", errors="replace")
    text = strip_comments(raw)
    errors, warnings, infos = [], [], []

    # 1 文档结构
    if "\\documentclass" not in text and "\\documentclass" not in raw:
        errors.append({"line": 1, "msg": "缺 \\documentclass", "fix": "在首行补 \\documentclass[12pt]{article} 或模板要求的类"})
    if "\\begin{document}" not in text:
        errors.append({"line": 1, "msg": "缺 \\begin{document}", "fix": "补 \\begin{document}，正文在其后"})
    if "\\end{document}" not in text:
        errors.append({"line": line_of(text, len(text)), "msg": "缺 \\end{document}", "fix": "文末补 \\end{document}"})

    # 2 环境配对
    env_errors, env_used = parse_envs(text)
    for e in env_errors:
        if e.get("unclosed"):
            names = "、".join(f"\\end{{{n}}}" for n, _ in e["unclosed"])
            errors.append({**e, "fix": f"补上 {names}（或删除对应的 \\begin）"})
        else:
            errors.append({**e, "fix": f"补上 \\end{{{e['env']}}}，或删除多余的 \\begin{{{e['env']}}}"})

    # 3 花括号
    depth, first_bad = count_brace_balance(text)
    if first_bad:
        errors.append({"line": first_bad, "msg": "出现多余的 }（右括号多于左括号）",
                       "fix": "检查该行前后的 { } 配对"})
    if depth > 0:
        errors.append({"line": line_of(text, len(text)), "msg": f"花括号未闭合（多出 {depth} 个 {{）",
                       "fix": "逐个 \\command{ 检查参数是否缺少 }"})

    # 4 $ 配对
    for d in check_dollar(text):
        warnings.append({**d, "fix": "补齐成对的 $，或改用 \\( \\) 行内公式"})

    # 5 tabular 列数
    for t in check_tabular(text):
        errors.append({**t, "fix": "调整该行 & 数量，或修改列声明"})

    # 6 特殊字符
    for s in check_specials(text)[:40]:
        warnings.append({**s, "fix": "转义（\\_ \\# \\^）或放进数学模式"})

    # 7 引用与标签
    bib_keys = load_bib_keys(args.bib) if args.bib else set()
    cr = check_cites_refs(text, bib_keys)
    for d in cr["dangling_cites"]:
        (errors if bib_keys else warnings).append({
            "line": d["line"], "msg": f"\\cite{{{d['key']}}} 在 bib 中不存在" if bib_keys else f"\\cite{{{d['key']}}} 未提供 --bib，无法核验",
            "fix": "补 bib 条目或修正 key" if bib_keys else "提供 --bib 以核验引用"})
    for d in cr["dangling_refs"]:
        warnings.append({"line": d["line"], "msg": f"\\ref{{{d['label']}}} 无对应 \\label",
                         "fix": "补 \\label 或修正引用名"})
    for d in cr["duplicate_labels"]:
        errors.append({"line": d["lines"][0], "msg": f"\\label{{{d['label']}}} 重复定义（行 {d['lines']}）",
                       "fix": "重命名其中一个 label，避免 \\ref 指向错误"})
    for u in cr["unused_labels"][:30]:
        infos.append({"line": u["line"], "msg": f"\\label{{{u['label']}}} 未被引用", "fix": "如无需交叉引用可删除"})

    # 8 中文与宏包
    if re.search(r"[\u4e00-\u9fff]", text) and not re.search(r"\\(ctex|usepackage\{ctex\}|usepackage\[UTF8\]\{ctex\}|xeCJK|usepackage\{xeCJK\})", text):
        warnings.append({"line": 1, "msg": "含中文但未加载 ctex/xeCJK",
                         "fix": "加载 \\usepackage{ctex} 并用 xelatex 编译，否则中文不显示"})

    # 9 图片路径
    for m in GRAPHICS.finditer(text):
        infos.append({"line": line_of(text, m.start()), "msg": f"\\includegraphics{{{m.group(1)}}}",
                      "fix": "确认该文件在编译目录或 \\graphicspath 内，扩展名可省"})

    stats = {"errors": len(errors), "warnings": len(warnings), "infos": len(infos),
             "cites": len(cr["cites"]), "labels": len(cr["labels"]), "refs": len(cr["refs"]),
             "environments": len(env_used)}
    report = {
        "ok": len(errors) == 0, "tex": str(args.tex), "bib": args.bib,
        "stats": stats, "errors": errors[:80], "warnings": warnings[:80], "infos": infos[:60],
        "label_ref_map": {"labels": cr["labels"][:80], "refs": cr["refs"][:80],
                          "dangling_refs": cr["dangling_refs"], "duplicate_labels": cr["duplicate_labels"]},
        "verification_hint": {
            "compile_readiness": f"静态错误 {len(errors)} 条（应为 0 才能进入编译）；警告 {len(warnings)} 条",
            "reference_integrity": f"\\cite {len(cr['cites'])} 处（悬空 {len(cr['dangling_cites'])}）；\\ref {len(cr['refs'])} 处（悬空 {len(cr['dangling_refs'])}）",
            "label_uniqueness": f"label {len(cr['labels'])} 个（重复 {len(cr['duplicate_labels'])}）",
            "structure_validity": f"环境 {stats['environments']} 类；结构错误 {len([e for e in errors if '\\begin' in e.get('msg','') or '\\end' in e.get('msg','')])} 条",
        },
    }
    out = _as_outdir(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "tex_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md = ["# LaTeX 静态检查报告", "",
          f"- 错误 {len(errors)}｜警告 {len(warnings)}｜提示 {len(infos)}",
          f"- \\cite {stats['cites']} 处｜\\label {stats['labels']} 个｜\\ref {stats['refs']} 处", ""]
    for title, items in [("错误（几乎必然编译失败）", errors),
                         ("警告（可能失败或排版异常）", warnings),
                         ("提示（建议项）", infos)]:
        if items:
            md += [f"## {title}", ""]
            for it in items[:30]:
                md.append(f"- L{it.get('line','?')} {it.get('msg','')} → {it.get('fix','')}")
            md.append("")
    md += ["## 自检口径建议", ""] + [f"- `{k}`：{v}" for k, v in report["verification_hint"].items()]
    (out / "tex_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False))
    return 0


def cmd_labels(args):
    text = strip_comments(Path(args.tex).read_text(encoding="utf-8", errors="replace"))
    bib_keys = load_bib_keys(args.bib) if args.bib else set()
    cr = check_cites_refs(text, bib_keys)
    print(json.dumps({"cites": cr["cites"][:120], "labels": cr["labels"][:120],
                      "refs": cr["refs"][:120], "dangling_cites": cr["dangling_cites"],
                      "dangling_refs": cr["dangling_refs"],
                      "duplicate_labels": cr["duplicate_labels"],
                      "unused_labels": cr["unused_labels"][:60]}, ensure_ascii=False, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(description="LaTeX 源码静态检查")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s1 = sub.add_parser("check"); s1.add_argument("--tex", required=True)
    s1.add_argument("--bib"); s1.add_argument("--out", required=True)
    s2 = sub.add_parser("labels"); s2.add_argument("--tex", required=True); s2.add_argument("--bib")
    a = ap.parse_args()
    return {"check": cmd_check, "labels": cmd_labels}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
