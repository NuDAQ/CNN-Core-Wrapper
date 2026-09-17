from pathlib import Path
import json
import hashlib
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class VerificationCliTest(unittest.TestCase):
    def test_qualifies_recovery_after_reset_in_each_transaction_phase(self):
        with tempfile.TemporaryDirectory(prefix="wrapper-recovery-") as tmp:
            run = subprocess.run([sys.executable, str(ROOT / "scripts/run_verilator_tests.py"),
                                  "--output", tmp], text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            report = json.loads((Path(tmp) / "manifest.json").read_text())["verification"]
            self.assertEqual(report["status"], "passed")
            for phase in ["reset-input", "reset-compute", "reset-output"]:
                self.assertIn(phase, report["scenarios"], "all reset phases must be qualified")
    def test_additional_reference_preserves_the_96_builtin_windows(self):
        with tempfile.TemporaryDirectory(prefix="wrapper-additive-") as tmp:
            root = Path(tmp)
            extra = root / "extra"
            extra.mkdir()
            (extra / "input.hex").write_text(("0"*128 + "\n")*32)
            # Independent committed Vitis result for one all-zero window.
            (extra / "expected.hex").write_text("001ff9c3\n")
            (extra / "reference.json").write_text(json.dumps({
                "windows": 1, "vitis_crosscheck_windows": 96,
                "ip_revision": "eca9b12f9f49f4b7324ed9ed241a44086ca9c842",
                "files": {name: hashlib.sha256((extra / name).read_bytes()).hexdigest()
                          for name in ["input.hex", "expected.hex"]},
            }))
            output = root / "run"
            run = subprocess.run([sys.executable, str(ROOT / "scripts/run_verilator_tests.py"),
                                  "--output", str(output), "--reference", str(extra),
                                  "--scenario", "baseline"], text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            report = json.loads((output / "manifest.json").read_text())["verification"]
            self.assertEqual(report["builtin_windows"], 96)
            self.assertEqual(report["additional_windows"], 1)
            self.assertEqual(report["windows"], 97)



if __name__ == "__main__":
    unittest.main()
