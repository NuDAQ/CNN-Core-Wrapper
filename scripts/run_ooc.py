#!/usr/bin/env python3
"""Build or prepare a standalone 200 MHz routed wrapper qualification."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from prepare_build import ROOT, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--core-root", type=Path)
    parser.add_argument("--prepare-only", action="store_true",
                        help="Prepare a portable directory for a Linux Vivado host")
    args = parser.parse_args()
    output = args.output.resolve()
    manifest = prepare(output, args.core_root)
    for source, name in [(ROOT / "scripts/run_ooc.tcl", "run_ooc.tcl"),
                         (ROOT / "hw/xdc/wrapper_ooc.xdc", "ooc.xdc")]:
        shutil.copyfile(source, output / name)
        manifest["files"].append({"path": name, "source": str(source),
                                  "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
    manifest["ooc"] = {"clock_source_site": "BUFGCE_X0Y0", "input_delay_ns": {"min": 0.0, "max": 1.0},
                       "output_delay_ns": {"min": 0.0, "max": 1.0},
                       "command": ["vivado", "-mode", "batch", "-source", "run_ooc.tcl"],
                       "status": "prepared"}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if args.prepare_only:
        print(f"Prepared {output}; run vivado -mode batch -source run_ooc.tcl in that directory")
        return
    subprocess.run(manifest["ooc"]["command"], cwd=output, check=True)
    result = json.loads((output / "result.json").read_text())
    if result["status"] != "passed":
        raise RuntimeError("OOC qualification did not pass")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
