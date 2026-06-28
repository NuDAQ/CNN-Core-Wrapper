# CNN Core Wrapper

Thin RTL wrapper for integrating the generated `cnn_core` block into a larger
ARIANNA trigger FPGA design.

The wrapper exposes a small control interface and AXI-Stream-style data ports,
then directly instantiates the CNN core provided by
`NuDAQ/CNN-Core-Generator`. This repository is intended to be used as an OOC
component or subsystem block, not as the final board-level top by itself.

## Interface

`WRAPPER_TOP` is defined in `hw/rtl/cnn_core_wrapper_top.v`.

- Control: `start`, `done`, `idle`, `ready`
- Input stream: 128-bit `input_data`, `input_valid`, `input_ready`
- Output stream: 32-bit `output_data`, `output_valid`, `output_ready`
- Core dependency: `cnn-core` version `3.4.2`

The wrapper maps these ports directly to the generated HLS RTL interface:
`input_layer_*`, `layer9_out_*`, and `ap_*`.

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

Run behavioral simulation and analysis with:

```sh
python3 scripts/run_behavioral_sim.py
```

The script resolves RTL sources through Bender, runs Vivado in batch mode, and
writes results under `out/behavioral_sim/`.

## Constraints

The wrapper is normally integrated as part of a larger system. In that flow,
package-pin constraints belong to the final board-level top, not to this OOC
wrapper. Use the files in `hw/xdc/` only when they match the intended synthesis
target and integration context.

## License

MIT License. See `LICENSE`.
