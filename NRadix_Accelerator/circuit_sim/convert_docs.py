#!/usr/bin/env python3
"""
Convert all NRadix markdown docs to styled HTML files.
Adds navigation, dark theme, and clickable links between docs.
"""

import markdown
import os
import re

FOLDER = "/home/jackwayne/Desktop/NRadix_Chip_Package"

# Files in reading order with descriptions
FILES = [
    ("TAPEOUT_READINESS", "Tape-Out Readiness Checklist"),
    ("CIRCUIT_SIMULATION_PLAN", "Circuit Simulation Plan & Results"),
    ("MONTE_CARLO_ANALYSIS", "Monte Carlo Yield Analysis"),
    ("THERMAL_SENSITIVITY", "Thermal Sensitivity Analysis"),
    ("CHIP_INTERFACE", "Chip Interface Specification"),
    ("DRC_RULES", "DRC Rules"),
    ("LAYER_MAPPING", "Foundry Layer Mapping"),
    ("MPW_RETICLE_PLAN", "MPW Reticle Plan"),
    ("FOUNDRY_SUBMISSION_PACKAGE", "Foundry Submission Package"),
    ("PACKAGING_SPEC", "Packaging Specification"),
    ("TEST_BENCH_DESIGN", "Test Bench Design & BOM"),
    ("FUNCTIONAL_TEST_PLAN", "Functional Test Plan"),
]

STYLE = """
<style>
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
    max-width: 900px;
    margin: 0 auto;
    padding: 20px 30px 60px 30px;
    background: #0f172a;
    color: #e2e8f0;
    line-height: 1.7;
    font-size: 15px;
  }
  h1 {
    color: #f59e0b;
    border-bottom: 2px solid #f59e0b;
    padding-bottom: 10px;
    margin-top: 30px;
    font-size: 26px;
  }
  h2 {
    color: #38bdf8;
    margin-top: 35px;
    padding-bottom: 5px;
    border-bottom: 1px solid #1e293b;
    font-size: 20px;
  }
  h3 { color: #a5b4fc; margin-top: 25px; font-size: 17px; }
  h4 { color: #94a3b8; margin-top: 20px; font-size: 15px; }
  a { color: #3b82f6; text-decoration: none; }
  a:hover { color: #f59e0b; text-decoration: underline; }
  table {
    border-collapse: collapse;
    width: 100%;
    margin: 15px 0;
    font-size: 14px;
  }
  th {
    background: #1e293b;
    color: #f59e0b;
    text-align: left;
    padding: 10px 12px;
    border: 1px solid #334155;
    font-weight: bold;
  }
  td {
    padding: 8px 12px;
    border: 1px solid #334155;
    vertical-align: top;
  }
  tr:nth-child(even) { background: #1e293b; }
  tr:hover { background: #334155; }
  code {
    background: #1e293b;
    color: #a5f3fc;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
  }
  pre {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 16px;
    overflow-x: auto;
    font-size: 13px;
    line-height: 1.5;
  }
  pre code {
    background: none;
    padding: 0;
    color: #a5f3fc;
  }
  blockquote {
    border-left: 4px solid #f59e0b;
    margin: 15px 0;
    padding: 10px 20px;
    background: #1e293b;
    border-radius: 0 8px 8px 0;
    color: #cbd5e1;
  }
  hr { border: none; border-top: 1px solid #334155; margin: 30px 0; }
  ul, ol { padding-left: 25px; }
  li { margin: 4px 0; }
  strong { color: #f1f5f9; }
  em { color: #94a3b8; }
  img { max-width: 100%; }

  /* Checkboxes */
  li { list-style-type: disc; }

  /* Navigation bar */
  .nav {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 12px 20px;
    margin-bottom: 25px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }
  .nav a {
    color: #3b82f6;
    font-size: 13px;
    font-weight: bold;
  }
  .nav .home { color: #f59e0b; font-size: 14px; }
  .nav .prev-next { display: flex; gap: 15px; }
  .nav .label { color: #64748b; font-size: 12px; }

  /* Checkbox styling for [x] and [ ] */
  .check-pass { color: #22c55e; font-weight: bold; }
  .check-open { color: #ef4444; font-weight: bold; }

  /* Status badges */
  .badge-pass {
    background: #166534;
    color: #22c55e;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
  }
  .badge-fail {
    background: #7f1d1d;
    color: #ef4444;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
  }
</style>
"""


def build_nav(current_idx):
    """Build navigation bar with prev/next links."""
    parts = []
    parts.append('<div class="nav">')
    parts.append('  <a class="home" href="START_HERE.html">Table of Contents</a>')
    parts.append('  <div class="prev-next">')

    if current_idx > 0:
        prev_name, prev_title = FILES[current_idx - 1]
        parts.append(f'    <a href="{prev_name}.html">&larr; {prev_title}</a>')

    if current_idx < len(FILES) - 1:
        next_name, next_title = FILES[current_idx + 1]
        parts.append(f'    <a href="{next_name}.html">{next_title} &rarr;</a>')

    parts.append('  </div>')
    parts.append('</div>')
    return "\n".join(parts)


def enhance_html(html_content):
    """Post-process HTML to add nice touches."""
    # Convert [x] and [ ] to styled checkboxes
    html_content = html_content.replace("[x]", '<span class="check-pass">[done]</span>')
    html_content = html_content.replace("[ ]", '<span class="check-open">[todo]</span>')

    # Bold **PASS** and **COMPLETE** in green
    html_content = re.sub(
        r'\*\*PASS\*\*',
        '<span style="color: #22c55e; font-weight: bold;">PASS</span>',
        html_content
    )
    html_content = re.sub(
        r'\*\*COMPLETE\*\*',
        '<span style="color: #22c55e; font-weight: bold;">COMPLETE</span>',
        html_content
    )
    html_content = re.sub(
        r'\*\*FAIL\*\*',
        '<span style="color: #ef4444; font-weight: bold;">FAIL</span>',
        html_content
    )

    # Convert .md links to .html links
    html_content = re.sub(r'href="([^"]+)\.md"', r'href="\1.html"', html_content)

    return html_content


def convert_file(name, title, idx):
    """Convert one markdown file to styled HTML."""
    md_path = os.path.join(FOLDER, f"{name}.md")

    if not os.path.exists(md_path):
        print(f"  SKIP: {md_path} not found")
        return

    with open(md_path, "r") as f:
        md_content = f.read()

    # Convert markdown to HTML
    md_converter = markdown.Markdown(
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
        output_format="html5",
    )
    body_html = md_converter.convert(md_content)
    body_html = enhance_html(body_html)

    nav = build_nav(idx)

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — N-Radix 9x9</title>
{STYLE}
</head>
<body>

{nav}

{body_html}

<hr>
{nav}

</body>
</html>"""

    html_path = os.path.join(FOLDER, f"{name}.html")
    with open(html_path, "w") as f:
        f.write(full_html)

    print(f"  OK: {name}.html")


def main():
    print(f"Converting {len(FILES)} docs to HTML...\n")

    for idx, (name, title) in enumerate(FILES):
        convert_file(name, title, idx)

    print(f"\nDone! All HTML files in: {FOLDER}")
    print("Open START_HERE.html to begin.")


if __name__ == "__main__":
    main()
