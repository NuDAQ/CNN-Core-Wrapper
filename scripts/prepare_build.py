#!/usr/bin/env python3
"""Prepare a reproducible, space-safe native CNN build directory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXPORT = Path("cnn_core/cnn_core_prj/solution1/impl/verilog")
PART = "xcku5p-ffvb676-2-e"


def command(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def prepare(output: Path, core_root: Path | None = None) -> dict:
    # Bender owns the dependency selection. An explicit checkout is recorded
    # as an override, never selected by searching stale checkout directories.
    override = core_root is not None
    if core_root is None:
        core_root = Path(command("bender", "path", "cnn-core", cwd=ROOT))
    core_root = core_root.resolve()
    export = core_root / EXPORT
    top = export / "cnn_core.v"
    if not top.is_file() or "layer12_out_TDATA" not in top.read_text():
        raise ValueError("Expected the native waveform/layer12_out CNN IP export")
    assets = sorted(p for p in export.iterdir() if p.suffix in {".v", ".vh", ".dat"})
    for path in assets:
        if path.suffix in {".v", ".vh"}:
            for filename in re.findall(r'\$readmemh\(\s*"([^"\n]+)"', path.read_text()):
                if not (export / filename).is_file():
                    raise ValueError(f"Missing ROM asset: {filename}")
    output = output.resolve()
    if any(output.iterdir()) if output.exists() else False:
        raise ValueError("Build directory must be empty; stale sources are not allowed")
    (output / "rtl").mkdir(parents=True, exist_ok=True)
    manifest = {
        "ip_revision": command("git", "rev-parse", "HEAD", cwd=core_root),
        "ip_dirty": bool(command("git", "status", "--porcelain", "--", str(EXPORT), cwd=core_root)),
        "core_root": str(core_root), "explicit_core_override": override,
        "wrapper_revision": command("git", "rev-parse", "HEAD", cwd=ROOT),
        "wrapper_dirty": bool(command("git", "status", "--porcelain", cwd=ROOT)),
        "part": PART, "clock_period_ns": 5.0, "files": [],
    }
    for source in [*assets, ROOT / "hw/rtl/cnn_core_wrapper_top.v"]:
        target = output / (source.name if source.suffix == ".dat" else "rtl/" + source.name)
        shutil.copyfile(source, target)
        manifest["files"].append({
            "path": str(target.relative_to(output)),
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "source": str(source),
        })
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--core-root", type=Path, help="Explicit checkout override, recorded in the manifest")
    args = parser.parse_args()
    try:
        manifest = prepare(args.output, args.core_root)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"ERROR: {error}\n")
    print(f"Prepared {len(manifest['files'])} assets from {manifest['ip_revision']}")


if __name__ == "__main__":
    main()
