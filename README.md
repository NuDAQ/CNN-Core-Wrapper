# CNN Core Wrapper

Thin RTL wrapper for integrating the generated `cnn_core` block into a larger
ARIANNA trigger FPGA design.

The wrapper exposes a small control interface and AXI-Stream-style data ports,
then adapts them to the CNN core provided by
`NuDAQ/CNN-Core-Generator`. This repository is intended to be used as an OOC
component or subsystem block, not as the final board-level top by itself.

## Interface

`WRAPPER_TOP` is defined in `hw/rtl/cnn_core_wrapper_top.v`.

- Control: `start`, `done`, `idle`, `ready`
- Input stream: 128-bit `input_data`, `input_valid`, `input_ready`
- Output stream: 32-bit `output_data`, `output_valid`, `output_ready`
- Core dependency: `cnn-core` version `4.1.0`

The generated CNN accepts 512-bit `waveform_*` words. The wrapper collects four
accepted 128-bit input beats into one word. The earliest beat is stored in bits
`[127:0]` and the latest beat is stored in bits `[511:384]`.

The CNN returns a signed `ap_fixed<23,13>` score. The wrapper converts it to the
existing signed `ap_fixed<22,11>` payload and keeps the 32-bit AXI container
zero-padded. Existing users can continue to compare signed bits `[21:0]`.

The 128-bit input word packs two consecutive 4-lane rows. Bits `[63:0]` carry
row 0 and bits `[127:64]` carry row 1; within each row, lane 0 is in the lowest
16-bit slot.

## Repository Layout

- `hw/rtl/` - wrapper RTL
- `hw/sim/` - SystemVerilog testbench
- `hw/xdc/` - timing and board-level constraint files
- `scripts/` - simulation and analysis helpers
- `out/` - generated simulation outputs
- `cnn_core_wrapper/` - Vivado project workspace

## Bender

Install or update dependencies with:

```sh
bender update
```

Generate a Vivado source script with:

```sh
bender script vivado > add_sources.tcl
```

## Simulation

Run the local interface tests with Verilator:

```sh
python3 scripts/run_verilator_tests.py
```

Run behavioral simulation and analysis with:

```sh
python3 scripts/run_behavioral_sim.py
```

The script resolves RTL sources through Bender, runs Vivado in batch mode, and
writes results under `out/behavioral_sim/`.

## License

MIT License. See `LICENSE`.
