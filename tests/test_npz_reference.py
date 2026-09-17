from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get("HLS_INCLUDE"), "requires the Linux Vitis HLS headers")
class NpzReferenceTest(unittest.TestCase):
    def test_supplied_npz_gets_a_bit_exact_reference_checked_against_vitis(self):
        core = Path(os.environ["CNN_CORE_ROOT"])
        npz = core / "data/verification_data_2cv_k5s3_f12_es0.npz"
        with tempfile.TemporaryDirectory(prefix="wrapper-reference-") as tmp:
            run = subprocess.run([sys.executable, str(ROOT / "scripts/build_reference.py"),
                                  "--core-root", str(core), "--npz", str(npz),
                                  "--hls-include", os.environ["HLS_INCLUDE"], "--output", tmp],
                                 text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            manifest = json.loads((Path(tmp) / "reference.json").read_text())
            self.assertEqual(manifest["windows"], 1000)
            self.assertEqual(manifest["vitis_crosscheck_windows"], 96)
            self.assertEqual(manifest["npz_sha256"], hashlib.sha256(npz.read_bytes()).hexdigest())
            self.assertEqual(len((Path(tmp) / "input.hex").read_text().splitlines()), 32000)
            self.assertEqual(len((Path(tmp) / "expected.hex").read_text().splitlines()), 1000)


if __name__ == "__main__":
    unittest.main()
