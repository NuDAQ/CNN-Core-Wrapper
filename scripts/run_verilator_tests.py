#!/usr/bin/env python3
"""Compile and run the local wrapper interface tests with Verilator."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "hw" / "rtl" / "cnn_core_wrapper_top.v"
TESTS = [ROOT / "tests" / "tb_wrapper_repack.sv"]


def main() -> int:
    verilator = shutil.which("verilator")
    if verilator is None:
        raise SystemExit("ERROR: verilator was not found on PATH")

    failures = 0
    for test in TESTS:
        top = test.stem
        print(f"[ RUN      ] {top}", flush=True)
        with tempfile.TemporaryDirectory(prefix=f"{top}-") as tmp:
            build_dir = Path(tmp)
            compile_result = subprocess.run(
                [
                    verilator,
                    "--binary",
                    "--timing",
                    "--assert",
                    "-Wall",
                    "-Wno-fatal",
                    "--top-module",
                    top,
                    "--Mdir",
                    str(build_dir),
                    str(WRAPPER),
                    str(test),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            if compile_result.returncode != 0:
                sys.stderr.write(compile_result.stdout)
                sys.stderr.write(compile_result.stderr)
                print(f"[  FAILED  ] {top}", flush=True)
                failures += 1
                continue

            run_result = subprocess.run(
                [str(build_dir / f"V{top}")],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            failed_output = "%Fatal" in run_result.stdout or "Assertion failed" in run_result.stdout
            if run_result.returncode != 0 or failed_output:
                sys.stderr.write(run_result.stdout)
                sys.stderr.write(run_result.stderr)
                print(f"[  FAILED  ] {top}", flush=True)
                failures += 1
                continue

            if run_result.stdout:
                print(run_result.stdout, end="")
            print(f"[       OK ] {top}", flush=True)

    print(f"Verilator: {len(TESTS) - failures} passed, {failures} failed, {len(TESTS)} total")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
