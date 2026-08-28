from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_behavioral_sim", ROOT / "scripts" / "run_behavioral_sim.py"
)
assert SPEC is not None and SPEC.loader is not None
RUN_BEHAVIORAL_SIM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN_BEHAVIORAL_SIM)


class SourceResolutionTest(unittest.TestCase):
    def test_checkout_fallback_finds_cnn_core_4_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            core_dir = (
                repo
                / ".bender"
                / "git"
                / "checkouts"
                / "cnn-core-test"
                / "cnn_core"
                / "cnn_core_prj"
                / "solution1"
                / "impl"
                / "verilog"
            )
            core_dir.mkdir(parents=True)
            (core_dir / "cnn_core.v").write_text("module cnn_core; endmodule\n")
            (core_dir / "cnn_core_helper.v").write_text("module cnn_core_helper; endmodule\n")

            rtl_files, sim_files = RUN_BEHAVIORAL_SIM.sources_from_checkout(repo)

            self.assertIn(core_dir / "cnn_core.v", rtl_files)
            self.assertIn(core_dir / "cnn_core_helper.v", rtl_files)
            self.assertEqual(sim_files, [repo / "hw" / "sim" / "tb_stream.sv"])


if __name__ == "__main__":
    unittest.main()
