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
    parser.add_argument("--reference", type=Path, help="Add a build_reference.py bundle to the built-in corpus")
    parser.add_argument("--scenario", choices=["all", "single", "baseline", "stalls", "reset-input", "reset-compute", "reset-output"], default="all")
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
    additional_windows = 0
    if args.reference:
        extra = args.reference.resolve()
        metadata = json.loads((extra / "reference.json").read_text())
        if metadata["ip_revision"] != manifest["ip_revision"] or metadata["vitis_crosscheck_windows"] != 96:
            raise RuntimeError("Additional reference does not match the verified native IP revision")
        for name in ["input.hex", "expected.hex"]:
            if hashlib.sha256((extra / name).read_bytes()).hexdigest() != metadata["files"][name]:
                raise RuntimeError(f"Additional reference hash mismatch: {name}")
        extra_words = (extra / "input.hex").read_text().splitlines()
        extra_scores = (extra / "expected.hex").read_text().splitlines()
        additional_windows = metadata["windows"]
        if additional_windows < 1 or len(extra_words) != 32*additional_windows or len(extra_scores) != additional_windows:
            raise RuntimeError("Incomplete additional reference corpus")
        for values, bits in [(extra_words, 512), (extra_scores, 32)]:
            if any(not re.fullmatch(r"[0-9a-fA-F]+", v) or int(v, 16) >= 2**bits for v in values):
                raise RuntimeError("Invalid raw reference word")
        words += extra_words
        scores += extra_scores
        manifest["additional_reference"] = metadata
    if len(scores) > 2048:
        raise RuntimeError("At most 2048 total windows are supported by the testbench")
    (output / "input.hex").write_text("\n".join(words) + "\n")
    (output / "expected.hex").write_text("\n".join(scores) + "\n")
    shutil.copyfile(ROOT / "tests/tb_native_wrapper.sv", output / "tb_native_wrapper.sv")
    build = ["verilator", "--binary", "--timing", "--assert", "--converge-limit", "10000",
             "-j", "4", "-Wno-fatal", "--top-module", "tb_native_wrapper", "--Mdir", "obj_dir",
             "-Irtl", "tb_native_wrapper.sv", *[str(p.relative_to(output)) for p in sorted((output / "rtl").glob("*.v"))]]
    print(f"Building actual IP RTL in {output}", flush=True)
    run(build, output, output / "build.log")
    scenarios = {"single": 0, "baseline": 0, "stalls": 1, "reset-input": 2, "reset-compute": 3, "reset-output": 4}
    selected = scenarios if args.scenario == "all" else {args.scenario: scenarios[args.scenario]}
    for name, mode in selected.items():
        window_count = 1 if name == "single" else len(scores)
        result = run([str((output / "obj_dir/Vtb_native_wrapper").resolve()),
                      f"+WINDOWS={window_count}", f"+SCENARIO={mode}"],
                     output, output / f"{name}.log")
        expected_summary = (f"PASS native windows={window_count} inputs={window_count*32} "
                            f"outputs={window_count} starts={window_count} done={window_count}")
        if expected_summary not in result:
            raise RuntimeError("Simulator did not report complete verification")
        print(result, end="")
    manifest["verification"] = {
        "verilator": subprocess.check_output(["verilator", "--version"], text=True).strip(),
        "compile_command": build, "windows": len(scores), "scenarios": list(selected), "status": "passed",
        "builtin_windows": 96, "additional_windows": additional_windows,
        "reference_sha256": hashlib.sha256(expected.read_bytes()).hexdigest(),
        "input_sha256": hashlib.sha256(inputs.read_bytes()).hexdigest(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Evidence: {output}")


if __name__ == "__main__":
    main()
