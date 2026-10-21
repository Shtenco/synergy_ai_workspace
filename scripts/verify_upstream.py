#!/usr/bin/env python3
"""Verify original SMM HTML assets are present and not placeholders."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
required = ["workspaces.html", "studio.html", "lead-radar.html", "caseflow.html"]
for filename in required:
    path = root / "upstream" / "smm" / filename
    if not path.is_file() or path.stat().st_size < 1000:
        sys.exit(f"FAIL: missing/incomplete original file: {path}")
    content = path.read_text(encoding="utf-8")
    if "<html" not in content.lower():
        sys.exit(f"FAIL: not an HTML original: {filename}")
    print(f"OK {filename} ({path.stat().st_size} bytes)")
print("Original SMM HTML presence check: PASS")
