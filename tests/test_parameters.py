from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ParameterContractTest(unittest.TestCase):
    def test_unsupported_shape_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="wrapper-parameters-") as tmp:
            work = Path(tmp)
            subprocess.run([sys.executable, str(ROOT / "scripts/prepare_build.py"),
                            "--output", str(work)], check=True, capture_output=True)
            (work / "invalid.sv").write_text("""
module invalid;
  WRAPPER_TOP #(.NUM_CHANNELS(3)) dut (
    .clk(1'b0), .rst_n(1'b0), .start(1'b0), .input_data(512'b0),
    .input_valid(1'b0), .output_ready(1'b0),
    .done(), .idle(), .ready(), .input_ready(), .output_data(), .output_valid());
  initial begin #1; $finish; end
endmodule
""")
            command = ["verilator", "--binary", "--timing", "--assert", "-Wno-fatal", "-j", "4",
                       "--converge-limit", "10000", "--top-module", "invalid", "-Irtl", "invalid.sv"]
            command += [str(p.relative_to(work)) for p in sorted((work / "rtl").glob("*.v"))]
            built = subprocess.run(command, cwd=work, text=True, capture_output=True)
            self.assertEqual(built.returncode, 0, built.stderr[-3000:])
            result = subprocess.run([str(work / "obj_dir/Vinvalid")], cwd=work,
                                    text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0, "unsupported shape was silently accepted")
            self.assertIn("WRAPPER_TOP requires 512/32-bit ports and a 256x4 window", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
