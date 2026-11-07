"""临时校验脚本 v2：判断渲染结果里究竟是真图还是错误提示。"""
import html
import pathlib
import re
import subprocess
import sys
import tempfile

md_path = pathlib.Path(sys.argv[1])
tmp = pathlib.Path(tempfile.mkdtemp(prefix="mmcheck2-"))
code = re.search(r"```mermaid\s*\n(.*?)```", md_path.read_text(encoding="utf-8"), re.S).group(1)
(tmp / "mermaid.min.js").write_bytes(pathlib.Path("tools/mermaid.min.js").read_bytes())
(tmp / "c.html").write_text(
    '<!doctype html><html><head><meta charset="utf-8">'
    '<script src="mermaid.min.js"></script></head><body>'
    '<div id="w"><pre class="mermaid">' + html.escape(code) + "</pre></div>"
    "<script>mermaid.initialize({startOnLoad:true,securityLevel:'loose'});</script>"
    "</body></html>",
    encoding="utf-8",
)
edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
out = tmp / "dom.html"
with open(out, "w", encoding="utf-8") as fh:
    subprocess.run(
        [edge, "--headless=old", "--disable-gpu", "--no-sandbox",
         f"--user-data-dir={tmp / 'prof'}", "--virtual-time-budget=8000",
         "--dump-dom", f"file:///{(tmp / 'c.html').as_posix()}"],
        stdout=fh, stderr=subprocess.DEVNULL, timeout=120,
    )
dom = out.read_text(encoding="utf-8", errors="replace")
print("file:", md_path)
print("  svg bytes        :", len(re.search(r"<svg.*?</svg>", dom, re.S).group(0)) if "<svg" in dom else 0)
print("  mindmap-node count:", dom.count('class="mindmap-node"'))
print("  nodeLabel count  :", dom.count("nodeLabel"))
print("  'Syntax error'   :", "Syntax error" in dom)
print("  marker 'error-text' occurrences:", dom.count("error-text"))
# 找出 svg 里所有 <text>/<tspan> 文本
texts = re.findall(r"<tspan[^>]*>(.*?)</tspan>", dom)
texts = [t for t in texts if t.strip()][:12]
print("  sample texts     :", texts)