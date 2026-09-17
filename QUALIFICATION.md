# Native CNN Wrapper Qualification

Date: 2026-09-17. Status: RTL verification passed; independent physical qualification is not yet complete. This is not a two-core system qualification.

## Source identity

- Generator: `eca9b12f9f49f4b7324ed9ed241a44086ca9c842`.
- Wrapper RTL SHA-256: `c9632e4e0ef2928732969d293acbf4f4e9542ffb84deb4242d3a62ffceaa4ba4`.
- Supplied NPZ SHA-256: `c662edb897f09ea93de1f524b1ce12f00e54b9b028565d4d2082d4c1bb0b64a4`.
- Development branch: `albert/native-cnn-wrapper`. Commits use the configured Albert identity.
- Local Bender 0.32.1 / Verilator 5.046; Ubuntu Vivado and Vitis HLS 2023.2.

## Functional evidence

The 96 committed Vitis windows are retained, and the user's 1,000 NPZ windows are additional coverage. The Linux C++ reference generator uses the unchanged generated firmware and vendor fixed-point types; both packed inputs and scores match all 96 existing Vitis transactions before the NPZ references are accepted.

All 1,096 windows pass bit for bit for continuous flow, legal input gaps with backpressure, and recovery after reset during input, computation, and a blocked output. Each full scenario checks 35,072 input handshakes, 1,096 results, 1,096 start/ready acknowledgements, 1,096 done events, and final idle. Separate one-shot verification checks one complete task and no extra work after stopping. A bare-IP instance verifies same-cycle public control/handshake behavior and valid output bits.

A deliberately incorrect 97th score causes a nonzero failure without a successful verification record. The local Python suite passes eight tests; one Linux-only reference-generation test is explicitly skipped locally and passes separately on Ubuntu.

## Physical evidence and current limitation

Two fresh routed attempts used `xcku5p-ffvb676-2-e` at 5.000 ns:

| Attempt | Result | Interpretation |
| --- | --- | --- |
| Initial XDC | Rejected by coverage gate | Unsupported XDC collection command left input delays unapplied; positive slack is invalid as qualification evidence. |
| Corrected full XDC, clock source BUFGCE_X0Y0 | WNS -1.989 ns, WHS -2.545 ns, WPWS +1.968 ns | Failed. Worst setup is internal to the first convolution; worst hold is at an input boundary. |

The second run's worst input hold path has 0 ns external launch-clock delay and 2.494 ns estimated internal capture-clock delay. A real same-clock source register is absent from a bare OOC boundary. This is being separated from genuine core routing limitations; no clock relaxation, broad false path, added wrapper pipeline, or generated-IP change has been used to claim a pass.

The user has been asked whether common-clock launch/capture registers may be used in a qualification-only harness, with the delivered wrapper remaining direct wiring and a 1 ns boundary budget retained. That acceptance change is pending.

AMD documents the distinction between external I/O delays and clock latency in [UG835 set_input_delay](https://docs.amd.com/r/2021.2-English/ug835-vivado-tcl-commands/set_input_delay). The reported path values above come from the actual routed design, not from the documentation.

## Artifact locations

- Local full-corpus RTL run: `/private/tmp/cnn-wrapper-full-1096`.
- Ubuntu job root: `/home/work1/Works/_codex_cnn_wrapper_native_20260917`.
- Ubuntu NPZ reference: `npz_reference/` below that job root.
- Failed OOC snapshots: `cnn-wrapper-ooc-finalsrc-20260917/` and `cnn-wrapper-ooc-constrained-20260917/` below the job root, including source manifests, complete logs, reports, and routed checkpoints.
- Working decisions and TDD history: `notes-untracked/PLAN.md` and `notes-untracked/PROGRESS.md`.

## Integration boundary

System changes remain follow-up work: two-core scheduling, 256-to-512 conversion, correct FIFO empty/backpressure handling, native score/threshold interpretation, metadata-capacity proof, real XPM CDC, and sustained dual-core qualification. Future single-core admission requires system capacity reservation and overlap; the current delivery makes no single-core throughput claim.
