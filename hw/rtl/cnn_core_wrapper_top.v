`timescale 1ns / 1ps

// Native CNN transport boundary. Task admission and metadata belong to the system.
module WRAPPER_TOP #(
    parameter INPUT_WIDTH = 512,
    parameter OUTPUT_WIDTH = 32,
    parameter NUM_TIMESTEPS = 256,
    parameter NUM_CHANNELS = 4
)(
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         start,
    output wire                         done,
    output wire                         idle,
    output wire                         ready,
    input  wire [INPUT_WIDTH-1:0]        input_data,
    input  wire                         input_valid,
    output wire                         input_ready,
    output wire [OUTPUT_WIDTH-1:0]       output_data,
    output wire                         output_valid,
    input  wire                         output_ready
);
    // No packing, score conversion, additional latency, or start scheduling.
    cnn_core cnn_core_inst (
        .ap_clk           (clk),
        .ap_rst_n         (rst_n),
        .ap_start         (start),
        .ap_done          (done),
        .ap_idle          (idle),
        .ap_ready         (ready),
        .waveform_TDATA   (input_data),
        .waveform_TVALID  (input_valid),
        .waveform_TREADY  (input_ready),
        .layer12_out_TDATA (output_data),
        .layer12_out_TVALID(output_valid),
        .layer12_out_TREADY(output_ready)
    );
endmodule
