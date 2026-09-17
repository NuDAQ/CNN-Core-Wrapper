from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OocEntryTest(unittest.TestCase):
    def test_standalone_build_does_not_add_constraints_to_consumers(self):
        with tempfile.TemporaryDirectory(prefix="wrapper-ooc-") as tmp:
            result = subprocess.run([sys.executable, str(ROOT / "scripts/run_ooc.py"),
                                     "--prepare-only", "--output", tmp],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            manifest = json.loads((Path(tmp) / "manifest.json").read_text())
            self.assertEqual(manifest["ooc"]["top"], "WRAPPER_OOC")
            self.assertEqual(manifest["ooc"]["boundary_max_ns"], 4.0)
            self.assertTrue((Path(tmp) / "rtl/wrapper_ooc_top.v").is_file())
            self.assertTrue((Path(tmp) / "run_ooc.tcl").is_file())
            self.assertTrue((Path(tmp) / "ooc.xdc").is_file())
            sources = subprocess.run(["bender", "sources", "-f", "-t", "fpga", "-t", "synthesis"],
                                     cwd=ROOT, text=True, capture_output=True, check=True)
            groups = json.loads(sources.stdout)
            constraints = [p for g in groups for p in g["files"] if p.endswith(".xdc")]
            self.assertEqual(constraints, [], "system consumers must own their constraints")
            self.assertFalse(any(p.endswith("wrapper_ooc_top.v") for g in groups for p in g["files"]),
                             "qualification registers must not enter production source lists")


if __name__ == "__main__":
    unittest.main()
