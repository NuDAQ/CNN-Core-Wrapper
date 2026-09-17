# CNN Core Wrapper

A thin, synchronous RTL boundary for the generated CNN IP. `WRAPPER_TOP` connects native data and control ports directly, adding no registers, FIFOs, scheduling, score conversion, or clock-cycle latency. The trigger system owns task admission, CDC, metadata, core assignment, and result arbitration.

## Interface

| Port | Contract |
| --- | --- |
| `clk` | CNN clock; independent qualification target is 200 MHz |
| `rst_n` | Active-low synchronous reset; discards in-flight work |
| `start`, `done`, `idle`, `ready` | Native `ap_ctrl_hs` controls |
| `input_data[511:0]`, `input_valid`, `input_ready` | Native input stream |
| `output_data[31:0]`, `output_valid`, `output_ready` | Native score stream |

A window has 256 time steps and four model channels, transferred as 32 input words. In word `w`, 16-bit slot `4*r+c` contains sample `[8*w+r][c]`, for `r=0..7` and `c=0..3`; lower indices occupy lower bits. The IP consumes signed bits `[9:0]` of each slot with five fractional bits:

```text
sample = signed(slot[9:0]) / 32
score  = signed(output_data[20:0]) / 512
```

Output bits `[31:21]` are zero-filled by the IP. Interpret the low 21 bits as signed before comparing thresholds. The wrapper preserves raw bits and does not perform the previous score scaling or upstream ADC clipping.

Each stream advances only on its own `valid && ready`. A source holds valid and payload while stalled. Input gaps and finite output backpressure are supported. Keep each start request asserted until its corresponding native ready event; after the last request is acknowledged, deassert start to avoid starting an extra task. `ready`, last-input acceptance, `done`, and result consumption are distinct events.

Reset invalidates all in-flight tasks without replacement results. The system must reset its corresponding metadata state. Invalid payload wires need not be zero during or after reset.

The retained parameters support exactly `INPUT_WIDTH=512`, `OUTPUT_WIDTH=32`, `NUM_TIMESTEPS=256`, and `NUM_CHANNELS=4`; unsupported values produce an error. There is no TLAST or task metadata interface.

## Dependencies

`Bender.yml` and `Bender.lock` pin CNN-Core-Generator revision `eca9b12f9f49f4b7324ed9ed241a44086ca9c842`. This repository uses a direct Bender manifest. Bender 0.32.1 was used for dependency resolution; no Bendis workspace migration is required.

```sh
bender update cnn-core
bender path cnn-core
```

A local override can change the resolved source. Every build records the actual revision, dirty status, source paths, and file hashes. `--core-root /path/to/CNN-Core-Generator` is an explicit diagnostic override; no script searches stale checkouts and silently selects one.

For system source generation:

```sh
bender script vivado -t fpga -t synthesis > /tmp/cnn-wrapper-sources.tcl
```

Consumer targets receive RTL and IP assets without wrapper-top XDC. The dedicated `cnn_wrapper_ooc` target enables standalone constraints; `cnn_wrapper_test` together with `simulation` enables the native testbench. Stage ROM `.dat` files at the simulation/build working directory when creating a separate consumer flow.

## RTL verification

Tested locally with Verilator 5.046 and Python 3.14. The actual generated IP runs alongside a bare-IP instance, with scores independently checked against committed Vitis RTL reference transactions. No model stub is used for qualification.

```sh
python3 scripts/run_verilator_tests.py
python3 -m unittest discover -s tests -v
```

The default RTL run covers one-shot control, continuous transactions, legal input gaps, input/output backpressure, and reset during input, computation, and a stalled output. It checks exact control and data counts, output stability, same-cycle public-port behavior, and final idle. A wrong score, incomplete run, assertion failure, or timeout fails verification. `run_behavioral_sim.py` is an alias for this same native Verilator flow.

The verifier creates a fresh temporary directory by default. Use `--output /path/to/empty-directory` to retain an explicit artifact location. That directory contains the staged RTL/ROM, testbench, vectors, build/scenario logs, and a hashed `manifest.json`.

### Add the supplied NPZ corpus

On Linux with Vitis HLS 2023.2 headers, G++ and NumPy, generate additional reference vectors from the same IP's HLS C++:

```sh
python3 -m pip install -r requirements-verification.txt
python3 scripts/build_reference.py \
  --core-root "$(bender path cnn-core)" \
  --npz /path/to/verification_data_2cv_k5s3_f12_es0.npz \
  --hls-include /tools/Xilinx/Vitis_HLS/2023.2/include \
  --output /tmp/cnn-npz-reference
```

The reference generator first checks all 96 committed Vitis input/output transactions, including native rounding, saturation, and packing, before exporting the NPZ vectors. Copy `input.hex`, `expected.hex`, and `reference.json` together to the machine running Verilator, then run:

```sh
python3 scripts/run_verilator_tests.py --reference /tmp/cnn-npz-reference
```

The 1,000 supplied windows augment the original 96, giving 1,096 windows per full scenario. The one-shot scenario uses one window. This verifies bit-level implementation behavior; classification labels and model quality are separate concerns. Up to 2,048 total windows are supported per verifier invocation.

The Linux reference-generation test can also be run with:

```sh
HLS_INCLUDE=/tools/Xilinx/Vitis_HLS/2023.2/include \
CNN_CORE_ROOT="$(bender path cnn-core)" \
python3 -m unittest discover -s tests -p test_npz_reference.py -v
```

Without those environment settings, the local suite explicitly skips that Linux-only test.

## Standalone routed OOC qualification

Tested with Vivado 2023.2 on `xcku5p-ffvb676-2-e`. Use a fresh output directory:

```sh
source /tools/Xilinx/Vivado/2023.2/settings64.sh
python3 scripts/run_ooc.py --output /tmp/cnn-wrapper-ooc
```

To prepare locally and run on a Linux host:

```sh
python3 scripts/run_ooc.py --prepare-only --output /tmp/cnn-wrapper-ooc
# Transfer the complete directory, including ROM files, without changing contents.
cd /path/to/transferred/cnn-wrapper-ooc
vivado -mode batch -source run_ooc.tcl
```

The flow performs fresh OOC synthesis, optimization, placement, physical optimization, and routing. Its declared standalone budget is a 5.000 ns clock, max/min input and output delays of 1.000/0.000 ns, and clock source site `BUFGCE_X0Y0` for OOC clock-delay estimation. Synchronous reset is timed. These are independent qualification assumptions; the integrated system owns its clock placement and timing environment.

Passing requires nonnegative setup, hold, and pulse-width slack, complete required timing coverage, completed routing, and no blocking DRCs. Failures exit nonzero. `result.json` is written only after the gates pass; reports, full Vivado logs, the source manifest, and `routed.dcp` provide the evidence. Historical GUI projects, board pin files, and old `out/` results are not inputs to this batch flow.

## System handoff

The intended next integration uses two cores. Update the system to:

1. Instantiate the 512-bit interface and decode signed 21-bit scores with nine fractional bits; update thresholds consistently.
2. Produce 512-bit words from its 256-bit ADC-side stream, with correct time/channel ordering and 32 accepted words per window.
3. Gate FIFO reads, stream validity, and counters by actual availability and successful handshakes.
4. Reuse lane metadata queues and result arbitration, while proving capacity under the new IP and backpressure.
5. Validate native start control, real XPM CDC, 250 MHz acquisition / 200 MHz CNN clocks, two-core sustained flow, and metadata association.

Future single-core admission must reserve enough system buffering to overlap acquisition and consumption. Improving single-core compute throughput is separate from this wrapper. Neither future work requires adding a task-management interface to the wrapper within the accepted data shape.

See `QUALIFICATION.md` for the delivery evidence and remaining integration boundary.
