#!/usr/bin/env python3
"""扫描 05-experiments/<项目>/ 下的 project.md 与 runs/*.md，
解析成结构化数据，内联进 dashboard/experiments.html。

新增一次实验：把机器产出的 md 丢进对应项目的 runs/，然后：
    python3 dashboard/build-experiments.py

md 格式（缩进式 frontmatter，便于无依赖解析）：
    ---
    project: ecot-uav
    run: r018-xxx
    date: 2026-06-12
    status: done            # done / running / failed / queued
    metrics:
      success_rate: 0.75
      vs_baseline: +0.03
    ---
    ## 观察
    ...
    ## 下一步想法
    ...
    ## 要读的论文
    ...
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_ROOT = ROOT / "05-experiments"
HTML_PATH = ROOT / "dashboard" / "experiments.html"
START, END = "<!-- DATA:START -->", "<!-- DATA:END -->"


def coerce(v: str):
    v = v.strip().strip('"').strip("'")
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d*\.\d+", v):
        return float(v)
    return v


def parse_md(text: str):
    fm, body = {}, text
    if text.lstrip().startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = parse_frontmatter(parts[1])
            body = parts[2]
    return fm, parse_sections(body), body.strip()


def parse_frontmatter(raw: str) -> dict:
    fm, cur = {}, None
    for line in raw.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^(\s*)([\w\-]+):\s*(.*)$", line)
        if not m:
            continue
        indent, key, val = len(m.group(1)), m.group(2), m.group(3).strip()
        if indent == 0:
            if val == "":
                fm[key] = {}
                cur = key
            else:
                fm[key] = coerce(val)
                cur = None
        elif cur and isinstance(fm.get(cur), dict):
            fm[cur][key] = coerce(val)
    return fm


def parse_sections(body: str) -> dict:
    secs, cur, buf = {}, None, []
    for line in body.splitlines():
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            if cur is not None:
                secs[cur] = "\n".join(buf).strip()
            cur, buf = m.group(1).strip(), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        secs[cur] = "\n".join(buf).strip()
    return secs


def main() -> int:
    if not EXP_ROOT.exists():
        print(f"找不到 {EXP_ROOT}", file=sys.stderr)
        return 1
    projects = []
    for proj_dir in sorted(p for p in EXP_ROOT.iterdir() if p.is_dir()):
        pmd = proj_dir / "project.md"
        if not pmd.exists():
            continue
        pfm, _, pbody = parse_md(pmd.read_text(encoding="utf-8"))
        runs = []
        runs_dir = proj_dir / "runs"
        if runs_dir.exists():
            for rf in sorted(runs_dir.glob("*.md")):
                rfm, rsecs, _ = parse_md(rf.read_text(encoding="utf-8"))
                runs.append({
                    "run": rfm.get("run", rf.stem),
                    "date": str(rfm.get("date", "")),
                    "status": rfm.get("status", ""),
                    "metrics": rfm.get("metrics", {}) if isinstance(rfm.get("metrics"), dict) else {},
                    "sections": rsecs,
                })
        runs.sort(key=lambda r: (r["date"], r["run"]))
        mk, mg = pfm.get("metric_key"), pfm.get("metric_goal", "max")
        best = None
        if mk:
            vals = [(r["run"], r["metrics"].get(mk)) for r in runs
                    if isinstance(r["metrics"].get(mk), (int, float))]
            if vals:
                pick = max(vals, key=lambda x: x[1]) if mg == "max" else min(vals, key=lambda x: x[1])
                best = {"run": pick[0], "metric": pick[1]}
        projects.append({
            "name": pfm.get("name", proj_dir.name),
            "slug": pfm.get("slug", proj_dir.name),
            "goal": pfm.get("goal", ""),
            "baseline": pfm.get("baseline", ""),
            "metric_key": mk,
            "metric_goal": mg,
            "desc": pbody,
            "runs": runs,
            "best": best,
        })

    data = {"projects": projects}
    pretty = json.dumps(data, ensure_ascii=False, indent=2).replace("</script>", "<\\/script>")
    block = (f"{START}\n"
             f'<script id="exp-data" type="application/json">\n{pretty}\n</script>\n'
             f"{END}")

    if not HTML_PATH.exists():
        print(f"找不到 {HTML_PATH}", file=sys.stderr)
        return 1
    html = HTML_PATH.read_text(encoding="utf-8")
    if START not in html or END not in html:
        print("experiments.html 里找不到 DATA 标记。", file=sys.stderr)
        return 1
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _m: block, html, count=1, flags=re.S)
    HTML_PATH.write_text(new, encoding="utf-8")

    total_runs = sum(len(p["runs"]) for p in projects)
    print(f"✓ 实验板已重建：{HTML_PATH}")
    print(f"  {len(projects)} 个项目 · {total_runs} 条 run")
    for p in projects:
        b = f"，最佳 {p['metric_key']}={p['best']['metric']}（{p['best']['run']}）" if p.get("best") else ""
        print(f"  - {p['name']}：{len(p['runs'])} run{b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
