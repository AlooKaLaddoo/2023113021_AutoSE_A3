#!/usr/bin/env python3
"""Render report.md to report.pdf: Python-Markdown to HTML (Mermaid diagrams rendered in the browser),
then headless Chromium prints it to PDF.

usage: <python with markdown installed> build_report.py
"""
import html
import re
import subprocess
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[2]
src = (ROOT / 'report.md').read_text()

# Python-Markdown (unlike GitHub) needs a blank line before a list and 4-space indents for nested items.
LIST = re.compile(r'^(\s*)([-*]|\d+\.) ')
lines, prev = [], ''
for line in src.split('\n'):
    m = LIST.match(line)
    if m:
        indent = len(m.group(1))
        if 0 < indent < 4:
            line = '    ' + line.lstrip()
        elif indent >= 4 and indent % 4:
            line = ' ' * (4 * ((indent + 3) // 4)) + line.lstrip()
        if prev.strip() and not LIST.match(prev) and not prev.startswith('|'):
            lines.append('')
    elif prev and LIST.match(prev) and line.startswith('  ') and not line.strip().startswith('|'):
        line = '    ' + line.lstrip()          # continuation paragraph of a list item
    lines.append(line)
    prev = line
src = '\n'.join(lines)
MERMAID = []


def _stash(m):
    MERMAID.append(m.group(1))
    return f'MERMAIDBLOCK{len(MERMAID) - 1}'


src = re.sub(r'```mermaid\n(.*?)```', _stash, src, flags=re.S)

body = markdown.markdown(src, extensions=['tables', 'fenced_code', 'sane_lists'])
body = body.replace('<h2>Appendix', '<h2 class="appendix">Appendix')
for i, code in enumerate(MERMAID):
    body = body.replace(f'<p>MERMAIDBLOCK{i}</p>', f'<div class="mermaid">{html.escape(code)}</div>')

css = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
body { font-family: 'DejaVu Sans', 'Liberation Sans', Arial, sans-serif; font-size: 9.6pt; line-height: 1.38;
       color: #111; }
h1 { font-size: 17pt; margin: 0 0 2pt 0; }
h1 + p { color: #555; margin-top: 0; }
h2 { font-size: 12.5pt; border-bottom: 1px solid #bbb; padding-bottom: 2pt; margin: 14pt 0 5pt; }
h3 { font-size: 10.5pt; margin: 10pt 0 3pt; }
p, li { margin: 3pt 0; }
ul, ol { padding-left: 18pt; margin: 3pt 0; }
table { border-collapse: collapse; width: 100%; margin: 5pt 0 7pt; font-size: 8.3pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th, td { border: 1px solid #c8c8c8; padding: 2.5pt 4pt; vertical-align: top; text-align: left; }
th { background: #f0f0f0; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.4pt; background: #f4f4f4; padding: 0 1.5pt;
       border-radius: 2px; }
pre { background: #f4f4f4; padding: 5pt; font-size: 8pt; white-space: pre-wrap; }
hr { border: none; margin: 4pt 0; }
blockquote { color: #444; border-left: 3px solid #ccc; margin: 4pt 0; padding-left: 8pt; }
h2.appendix { page-break-before: always; }
.mermaid { text-align: center; margin: 4pt 0; page-break-inside: avoid; }
.mermaid svg { max-height: 150mm; }
"""
html = f"""<!doctype html><html><head><meta charset="utf-8"><title>AutoSE A3 Report</title>
<style>{css}</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad: true, theme: 'neutral', flowchart: {{useMaxWidth: true}}, sequence: {{useMaxWidth: true, wrap: true, width: 130, messageFontSize: 14, actorFontSize: 13}}}});</script></head><body>{body}</body></html>"""
out_html = ROOT / 'report.html'
out_html.write_text(html)
pdf = ROOT / 'report.pdf'
r = subprocess.run(['chromium', '--headless', '--disable-gpu', '--no-pdf-header-footer', '--virtual-time-budget=15000',
                    f'--print-to-pdf={pdf}', out_html.as_uri()], capture_output=True, text=True)
out_html.unlink()
if r.returncode != 0 or not pdf.exists():
    sys.exit(r.stderr)
print('wrote', pdf)
