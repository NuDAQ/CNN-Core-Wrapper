#!/usr/bin/env python3
"""Build additive NPZ reference vectors using the pinned HLS C++ and Vitis types."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, cwd, log):
    with log.open("w") as stream:
        result = subprocess.run(command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"Command failed; see {log}:\n{log.read_text()[-4000:]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-root", type=Path, required=True)
    parser.add_argument("--npz", type=Path, required=True)
    parser.add_argument("--hls-include", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    core, output = args.core_root.resolve(), args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("output directory must be empty")
    output.mkdir(parents=True, exist_ok=True)
    firmware = core / "cnn_core/firmware"
    original = core / "cnn_core/tb_data/tb_input_features.dat"
    baseline = np.loadtxt(original, dtype=np.float32)
    with np.load(args.npz, allow_pickle=False) as data:
        x = data["X"]
        if x.shape[1:] not in [(256, 4), (256, 4, 1)] or len(x) == 0 or not np.isfinite(x).all():
            parser.error("X must contain finite 256x4 windows")
        x = x.reshape(len(x), 1024).astype(np.float32)
    if baseline.shape != (96, 1024):
        parser.error("expected the complete 96-window committed Vitis corpus")
    combined = np.concatenate([baseline, x]).astype("<f4")
    combined.tofile(output / "features.f32")
    shutil.copytree(firmware / "weights", output / "weights")
    harness = ROOT / "scripts/native_reference.cpp"
    shutil.copyfile(harness, output / "native_reference.cpp")
    compile_command = ["g++", "-std=c++14", "-O2", "-Wno-unknown-pragmas",
                       "-I" + str(args.hls_include.resolve()), "-I" + str(firmware),
                       str(firmware / "cnn_core.cpp"), "native_reference.cpp", "-lgmp", "-o", "native_reference"]
    run(compile_command, output, output / "compile.log")
    run([str(output / "native_reference"), str(len(combined))], output, output / "csim.log")
    words = (output / "all_input.hex").read_text().splitlines()
    scores = (output / "all_expected.hex").read_text().splitlines()
    if len(words) != len(combined)*32 or len(scores) != len(combined):
        raise RuntimeError("C++ reference did not complete every window")
    tv = core / "cnn_core/cnn_core_prj/solution1/sim/tv"
    ref_input = tv / "cdatafile/c.cnn_core.autotvin_waveform.dat"
    ref_output = tv / "rtldatafile/rtl.cnn_core.autotvout_layer12_out.dat"
    original_words = re.findall(r"^0x([0-9a-fA-F]+)$", ref_input.read_text(), re.M)
    original_scores = re.findall(r"^0x([0-9a-fA-F]+)$", ref_output.read_text(), re.M)
    if [int(w, 16) for w in words[:96*32]] != [int(w, 16) for w in original_words]:
        raise RuntimeError("HLS input conversion disagrees with committed Vitis transactions")
    if [int(w, 16) for w in scores[:96]] != [int(w, 16) for w in original_scores]:
        raise RuntimeError("HLS C++ scores disagree with committed Vitis RTL results")
    (output / "input.hex").write_text("\n".join(words[96*32:]) + "\n")
    (output / "expected.hex").write_text("\n".join(scores[96:]) + "\n")
    manifest = {
        "windows": len(x), "vitis_crosscheck_windows": 96,
        "npz_sha256": sha(args.npz),
        "ip_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=core, text=True).strip(),
        "compile_command": compile_command,
        "compiler": subprocess.check_output(["g++", "--version"], text=True).splitlines()[0],
        "hls_include": str(args.hls_include.resolve()), "ap_fixed_header_sha256": sha(args.hls_include / "ap_fixed.h"),
        "harness_sha256": sha(harness),
        "firmware": {str(p.relative_to(firmware)): sha(p) for p in sorted(firmware.rglob("*")) if p.is_file()},
        "files": {name: sha(output / name) for name in ["input.hex", "expected.hex"]},
        "vitis_reference_sha256": sha(ref_output), "baseline_input_sha256": sha(original),
    }
    (output / "reference.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"PASS reference windows={len(x)} Vitis-crosscheck=96; {output}")


if __name__ == "__main__":
    main()
