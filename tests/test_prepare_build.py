from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT.parent / "CNN-Core-Generator"


class PrepareBuildTest(unittest.TestCase):
    def test_prepares_native_ip_with_runtime_rom_assets(self):
        with tempfile.TemporaryDirectory(prefix="wrapper-assets-") as tmp:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/prepare_build.py"),
                 "--core-root", str(CORE), "--output", tmp],
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            manifest = json.loads((Path(tmp) / "manifest.json").read_text())
            self.assertEqual(manifest["ip_revision"],
                             "eca9b12f9f49f4b7324ed9ed241a44086ca9c842")
            self.assertEqual(manifest["part"], "xcku5p-ffvb676-2-e")
            rtl = Path(tmp) / "rtl"
            self.assertIn("layer12_out_TDATA", (rtl / "cnn_core.v").read_text())
            self.assertTrue(list(Path(tmp).glob("*.dat")), "ROM assets are required at runtime")
            self.assertTrue(all((Path(tmp) / entry["path"]).is_file()
                                for entry in manifest["files"]))


if __name__ == "__main__":
    unittest.main()
