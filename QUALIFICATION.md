# Native CNN Wrapper Qualification

Date: 2026-09-17. Status: independent wrapper delivery passed actual-IP RTL verification and routed 200 MHz qualification. Two-core system integration and board validation remain separate work.

## Source identity

- Generator: `eca9b12f9f49f4b7324ed9ed241a44086ca9c842` (Bender dependency and lockfile).
- Wrapper RTL SHA-256: `c9632e4e0ef2928732969d293acbf4f4e9542ffb84deb4242d3a62ffceaa4ba4`.
- Full RTL verification snapshot: wrapper commit `8e3324a331ef153ba96d82f612ae3556d2c0c2b9`, clean at preparation.
- Physical qualification snapshot: wrapper commit `7b09964`, clean at preparation. Its production RTL is identical to the functional snapshot; only the isolated physical fixture/flow changed.
- Supplied NPZ SHA-256: `c662edb897f09ea93de1f524b1ce12f00e54b9b028565d4d2082d4c1bb0b64a4`.
- Development branch: `albert/native-cnn-wrapper`. Commits use the configured Albert identity.
- Local Bender 0.32.1 / Verilator 5.046; Ubuntu Vivado and Vitis HLS 2023.2.

## Functional evidence

The 96 committed Vitis windows are retained, and the user's 1,000 NPZ windows are additional coverage. The Linux C++ reference generator uses the unchanged generated firmware and vendor fixed-point types; both packed inputs and scores match all 96 existing Vitis transactions before the NPZ references are accepted.

All 1,096 windows pass bit for bit for continuous flow, legal input gaps with backpressure, and recovery after reset during input, computation, and a blocked output. Each full scenario checks 35,072 input handshakes, 1,096 results, 1,096 start/ready acknowledgements, 1,096 done events, and final idle. Separate one-shot verification checks one complete task and no extra work after stopping. A bare-IP instance verifies same-cycle public control/handshake behavior and valid output bits.

The stalls scenario exercises 69,124 source-gap cycles, 7,986 input-stalled cycles, and 12,553 output-stalled cycles. Reset tests abort after seven input transfers, after all 32 inputs before the result, and while the old result has been blocked for four cycles. Each then recovers and checks the entire reference corpus.

A deliberately incorrect 97th score causes a nonzero failure without a successful verification record. All eight locally applicable Python tests pass; the Linux-only reference-generation test is explicitly skipped locally and passes separately on Ubuntu. One local test required authorized Bender lock-file access after the sandbox blocked it; that test passed on rerun.

## Routed physical evidence

Vivado 2023.2 completed fresh synthesis, optimization, placement, physical optimization, and routing for `xcku5p-ffvb676-2-e`.

| Acceptance item | Result |
| --- | --- |
| Clock period | 5.000 ns (200 MHz) |
| DUT launch/capture boundary requirement | 4.000 ns, reserving 1 ns |
| Setup WNS / total negative slack | +0.166 ns / 0 |
| Hold WHS / total hold slack | +0.010 ns / 0 |
| Pulse-width WPWS | +1.968 ns |
| Required clock, internal-endpoint, and I/O-delay coverage checks | All zero violations |
| Boundary-path coverage | Both banks present; actual timed paths have the required 4 ns budget |
| Routing / blocking DRC | Complete / none |

The user-approved `WRAPPER_OOC` fixture adds common-BUFG-clocked launch/capture registers around the unchanged wrapper. Only the fixture's external pin-to-launch-register and capture-register-to-pin paths are excluded. Normal setup/hold checks, synchronous reset paths, and all DUT data/control paths remain active. The fixture is not a functional streaming adapter and is excluded from normal consumer sources. Its registers add no latency or area to the delivered wrapper.

The worst setup path is the timed synchronous-reset launch path into the second convolution, under the 4 ns boundary budget. The routed `u_wrapper` hierarchy uses 28,215 LUTs, 19,268 FFs, and 64 DSPs, with no block RAM or URAM. The fixture adds 553 FFs outside that hierarchy. Placement/optimization can attribute buffers to the wrapper hierarchy even though its source RTL is direct wiring.

The methodology report has zero violations. The DRC report retains 55 DSP-pipelining warnings and one no-routable-load warning, with no error or critical-warning violations; these reports are archived without suppressing the warnings.

The positive margins qualify this standalone configuration. They do not establish extra frequency headroom or timing closure after duplicating the core, changing placement, or integrating system CDC and arbitration.

### Rejected attempts retained for traceability

| Attempt | Result | Interpretation |
| --- | --- | --- |
| Initial bare-top XDC | Rejected by coverage gate | Unsupported XDC collection command left input delays unapplied; positive slack was not accepted. |
| Corrected bare-top XDC with estimated clock source | WNS -1.989 ns, WHS -2.545 ns | Failed; worst setup was internal and worst hold was at the bare input boundary. |
| Approved common-clock fixture | WNS +0.166 ns, WHS +0.010 ns | Passed the complete qualification gates. |

The bare-top hold path used 0 ns external launch-clock delay against 2.494 ns estimated internal capture-clock delay. The approved fixture supplies actual common-clock register endpoints. No generated-IP edit, clock relaxation, DUT false path, or production-wrapper pipeline was used. AMD describes external I/O delays and clock latency in [UG835 set_input_delay](https://docs.amd.com/r/2021.2-English/ug835-vivado-tcl-commands/set_input_delay); reported measurements come from the actual implementation reports.

## Artifact locations and replay

Local evidence is retained below `notes-untracked/evidence/` (intentionally untracked):

- `rtl-final/`: staged RTL/ROM, testbench, combined vectors, hashed manifest, build log, and six scenario logs.
- `npz-reference/`: the additional 1,000 input/score windows and their reference provenance.
- `ooc-passed/`: hashed staged sources, constraints, scripts, full Vivado logs, timing/coverage/routing/DRC/resource reports, `result.json`, and routed-checkpoint hash.
- `failed-ooc-evidence.tgz`: both rejected physical attempts' reports, manifests, constraints, and logs.

The Ubuntu job root is `/home/work1/Works/_codex_cnn_wrapper_native_20260917`. Its `cnn-wrapper-ooc-harness-20260917/routed.dcp` retains the routed checkpoint; `npz_reference/` retains the complete C++ reference build. The previous physical snapshots are also retained there. The README gives fresh-build commands; manifests record exact input identities and commands.

## Integration boundary

System changes remain follow-up work: two-core scheduling, 256-to-512 conversion, correct FIFO empty/backpressure handling, native score/threshold interpretation, metadata-capacity proof, real XPM CDC, and sustained dual-core qualification. Reuse the existing system's metadata queues and arbitration; the wrapper adds none. Future single-core admission requires system capacity reservation and overlap; the current delivery makes no single-core throughput claim.
