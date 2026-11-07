#!/usr/bin/env python3
"""把 Markdown 里的第一个 mermaid 代码块渲染成 PNG（本地无头浏览器，不依赖在线服务）。

用法:
    python tools/render_mermaid.py <in.md> <out.png> [--width 2400] [--height 1600]

依赖:
    - tools/mermaid.min.js    （Mermaid 11 打包文件）
    - Microsoft Edge          （Windows 自带，--headless 截图）

2026-11 起 mermaid.ink / kroki 在本机网络下不稳定，因此改用本地渲染，
保证离线也能出图，且渲染结果可复现。
"""
from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
MERMAID_JS = TOOLS_DIR / "mermaid.min.js"
MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<style>
  html, body {{ margin:0; padding:0; background:#ffffff; }}
  body {{ font-family: "Microsoft YaHei","Segoe UI",sans-serif; }}
  #wrap {{ display:block; padding:32px; }}
  /* mermaid 默认 width:100%，在 inline-block 容器里会塌缩，这里强制按 viewBox 原始尺寸渲染 */
  #wrap svg {{ width:auto !important; height:auto !important; max-width:none !important; }}
</style>
<script src="mermaid.min.js"></script>
</head>
<body>
<div id="wrap"><pre class="mermaid">
{code}
</pre></div>
<script>
  mermaid.initialize({{ startOnLoad: true, securityLevel: 'loose', theme: 'default',
                        mindmap: {{ padding: 12 }} }});
</script>
</body></html>
"""


def extract_mermaid(md_text: str) -> str:
    m = re.search(r"```mermaid\s*\n(.*?)```", md_text, re.S)
    if not m:
        raise SystemExit("未找到 ```mermaid 代码块")
    return m.group(1).strip("\n")


def find_edge() -> str:
    for p in EDGE_CANDIDATES:
        if Path(p).exists():
            return p
    raise SystemExit("未找到 Microsoft Edge，无法渲染 Mermaid")


def crop_whitespace(png: Path, pad: int = 24) -> None:
    from PIL import Image, ImageChops

    im = Image.open(png).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    diff = ImageChops.difference(im, bg)
    bbox = diff.getbbox()
    if not bbox:
        return
    left, top, right, bottom = bbox
    left, top = max(0, left - pad), max(0, top - pad)
    right, bottom = min(im.width, right + pad), min(im.height, bottom + pad)
    im.crop((left, top, right, bottom)).save(png)


def ensure_mermaid_js() -> Path:
    """优先用本地副本；没有就下载一次并缓存（mermaid.min.js 不入版本库）。"""
    if MERMAID_JS.exists() and MERMAID_JS.stat().st_size > 500_000:
        return MERMAID_JS
    import urllib.request

    print(f"下载 Mermaid: {MERMAID_CDN}")
    MERMAID_JS.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(MERMAID_CDN, MERMAID_JS)
    return MERMAID_JS


def render(md_path: Path, out_path: Path, width: int, height: int) -> Path:
    js = ensure_mermaid_js()
    code = extract_mermaid(md_path.read_text(encoding="utf-8"))

    tmp = Path(tempfile.mkdtemp(prefix="mmrender-"))
    try:
        shutil.copy(js, tmp / "mermaid.min.js")
        (tmp / "d.html").write_text(
            HTML_TEMPLATE.format(code=html.escape(code)), encoding="utf-8"
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # Edge 的 --screenshot 对非 ASCII 路径不友好，先截到临时目录再搬过去
        shot = tmp / "shot.png"
        cmd = [
            find_edge(),
            "--headless=old",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--force-device-scale-factor=2",
            f"--window-size={width},{height}",
            f"--user-data-dir={tmp / 'profile'}",
            "--no-first-run",
            "--no-default-browser-check",
            "--virtual-time-budget=10000",
            f"--screenshot={shot}",
            f"file:///{(tmp / 'd.html').as_posix()}",
        ]
        subprocess.run(cmd, capture_output=True, timeout=180)
        if not shot.exists():
            raise SystemExit("render failed: Edge produced no screenshot")
        crop_whitespace(shot)
        shutil.move(str(shot), str(out_path))
        return out_path
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Markdown 中的 mermaid 代码块 → PNG")
    ap.add_argument("md", type=Path)
    ap.add_argument("png", type=Path)
    ap.add_argument("--width", type=int, default=2400)
    ap.add_argument("--height", type=int, default=1800)
    args = ap.parse_args()
    out = render(args.md, args.png, args.width, args.height)
    from PIL import Image

    print(f"OK -> {out} ({Image.open(out).size[0]}x{Image.open(out).size[1]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())