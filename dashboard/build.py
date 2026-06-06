#!/usr/bin/env python3
"""把 paper-vault/pipeline.json 内联进 dashboard/pipeline.html。

为什么需要它：双击用 file:// 打开网页时，浏览器会用 CORS 拦截对本地 JSON 的 fetch，
所以数据不能用 fetch 读，而是构建时内联进 HTML。改完 JSON 跑一下本脚本即可刷新看板。

用法：
    python3 dashboard/build.py
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "paper-vault" / "pipeline.json"
HTML_PATH = ROOT / "dashboard" / "pipeline.html"
START, END = "<!-- DATA:START -->", "<!-- DATA:END -->"


def main() -> int:
    if not JSON_PATH.exists():
        print(f"找不到 {JSON_PATH}", file=sys.stderr); return 1
    if not HTML_PATH.exists():
        print(f"找不到 {HTML_PATH}", file=sys.stderr); return 1

    # 校验 JSON 合法
    raw = JSON_PATH.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"pipeline.json 不是合法 JSON：{e}", file=sys.stderr); return 1

    pretty = json.dumps(data, ensure_ascii=False, indent=2)
    # 安全：避免 JSON 里出现的 </script> 提前结束脚本块
    pretty = pretty.replace("</script>", "<\\/script>")

    block = (f"{START}\n"
             f'<script id="pipeline-data" type="application/json">\n'
             f"{pretty}\n"
             f"</script>\n"
             f"{END}")

    html = HTML_PATH.read_text(encoding="utf-8")
    if START not in html or END not in html:
        print("pipeline.html 里找不到 DATA 标记，无法注入。", file=sys.stderr); return 1

    new_html = re.sub(re.escape(START) + r".*?" + re.escape(END),
                      lambda _m: block, html, count=1, flags=re.S)
    HTML_PATH.write_text(new_html, encoding="utf-8")

    n_papers = len(data.get("papers", []))
    n_skills = sum(len(s.get("skills", [])) for s in data.get("stages", []))
    print(f"✓ 看板已重建：{HTML_PATH}")
    print(f"  内联：{len(data.get('stages', []))} 阶段 · {n_skills} skill · {n_papers} 篇论文")
    print(f"  打开：open {HTML_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
