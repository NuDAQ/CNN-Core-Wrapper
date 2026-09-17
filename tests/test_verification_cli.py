from pathlib import Path
import json
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


if __name__ == "__main__":
    unittest.main()
