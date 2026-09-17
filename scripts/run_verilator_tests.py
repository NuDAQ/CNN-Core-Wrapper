#!/usr/bin/env python3
"""Verify the public wrapper against the actual native IP and Vitis reference."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from prepare_build import ROOT, prepare


def run(command, cwd, log):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    text = result.stdout + result.stderr
    log.write_text(text)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}); see {log}\n{text[-4000:]}")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or Path(tempfile.mkdtemp(prefix="cnn-wrapper-rtl-"))
    manifest = prepare(output, args.core_root)
    core = Path(manifest["core_root"])
    tv = core / "cnn_core/cnn_core_prj/solution1/sim/tv"
    inputs = tv / "cdatafile/c.cnn_core.autotvin_waveform.dat"
    expected = tv / "rtldatafile/rtl.cnn_core.autotvout_layer12_out.dat"
    words = re.findall(r"^0x([0-9a-fA-F]+)$", inputs.read_text(), re.M)
    scores = re.findall(r"^0x([0-9a-fA-F]+)$", expected.read_text(), re.M)
    if len(scores) != 96 or len(words) != 32*len(scores):
        raise RuntimeError("Incomplete Vitis reference corpus; expected 96 windows")
    (output / "input.hex").write_text("\n".join(words) + "\n")
    (output / "expected.hex").write_text("\n".join(scores) + "\n")
    shutil.copyfile(ROOT / "tests/tb_native_wrapper.sv", output / "tb_native_wrapper.sv")
    build = ["verilator", "--binary", "--timing", "--assert", "--converge-limit", "10000",
             "-j", "4", "-Wno-fatal", "--top-module", "tb_native_wrapper", "--Mdir", "obj_dir",
             "-Irtl", "tb_native_wrapper.sv", *[str(p.relative_to(output)) for p in sorted((output / "rtl").glob("*.v"))]]
    print(f"Building actual IP RTL in {output}", flush=True)
    run(build, output, output / "build.log")
    result = run([str((output / "obj_dir/Vtb_native_wrapper").resolve()), f"+WINDOWS={len(scores)}"],
                 output, output / "simulation.log")
    expected_summary = "PASS native windows=96 inputs=3072 outputs=96 starts=96 done=96"
    if expected_summary not in result:
        raise RuntimeError("Simulator did not report complete verification")
    manifest["verification"] = {
        "verilator": subprocess.check_output(["verilator", "--version"], text=True).strip(),
        "compile_command": build, "windows": len(scores), "status": "passed",
        "reference_sha256": hashlib.sha256(expected.read_bytes()).hexdigest(),
        "input_sha256": hashlib.sha256(inputs.read_bytes()).hexdigest(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(result, end="")
    print(f"Evidence: {output}")


if __name__ == "__main__":
    main()
