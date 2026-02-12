`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: University of California, Irvine
// Engineer: Albert L. Cheung
// 
// Create Date: 02/11/2026 04:44:24 PM
// Design Name: CNN Core Wrapper
// Module Name: cnn_core_wrapper_top
// Project Name: CNN Core Wrapper
// Target Devices: xcku5p-ffvb676-2-e
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////

module WRAPPER_TOP #(
    parameter INPUT_WIDTH = 64,
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

    input  wire [INPUT_WIDTH-1:0]       input_data,
    input  wire                         input_valid,
    output wire                         input_ready,

    output wire [OUTPUT_WIDTH-1:0]      output_data,
    output wire                         output_valid,
    input  wire                         output_ready
);

    // Internal Signals
    wire [INPUT_WIDTH-1:0]       input_axis_tdata;
    wire                         input_axis_tvalid;
    wire                         input_axis_tready;

    wire [OUTPUT_WIDTH-1:0]      output_axis_tdata;
    wire                         output_axis_tvalid;
    wire                         output_axis_tready;

    wire                         ap_start;
    wire                         ap_done;
    wire                         ap_idle;
    wire                         ap_ready;

    // Connections
    assign input_axis_tdata  = input_data;
    assign input_axis_tvalid = input_valid;
    assign input_ready       = input_axis_tready;

    assign output_data       = output_axis_tdata;
    assign output_valid      = output_axis_tvalid;
    assign output_axis_tready = output_ready;

    assign ap_start = start;
    assign done  = ap_done;
    assign idle  = ap_idle;
    assign ready = ap_ready;

    // IP Instance
    cnn_core_0 cnn_core_0 (
        .ap_clk              (clk),
        .ap_rst_n            (rst_n),
        .ap_start            (ap_start),
        .ap_done             (ap_done),
        .ap_idle             (ap_idle),
        .ap_ready            (ap_ready),
        .input_layer_TDATA   (input_axis_tdata),
        .input_layer_TVALID  (input_axis_tvalid),
        .input_layer_TREADY  (input_axis_tready),
        .layer10_out_TDATA   (output_axis_tdata),
        .layer10_out_TVALID  (output_axis_tvalid),
        .layer10_out_TREADY  (output_axis_tready)
    );

endmodule