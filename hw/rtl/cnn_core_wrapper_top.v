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
    parameter INPUT_WIDTH = 128,
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
    reg  [511:0]                 input_axis_tdata;
    reg                          input_axis_tvalid;
    wire                         input_axis_tready;
    reg  [1:0]                   input_beat_count;

    wire [OUTPUT_WIDTH-1:0]      output_axis_tdata;
    wire                         output_axis_tvalid;
    wire                         output_axis_tready;
    wire [21:0]                  output_compat_tdata;

    wire                         ap_start;
    wire                         ap_done;
    wire                         ap_idle;
    wire                         ap_ready;

    // Connections
    assign input_ready = !input_axis_tvalid || input_axis_tready;

    always @(posedge clk) begin
        if (!rst_n) begin
            input_axis_tdata  <= 512'b0;
            input_axis_tvalid <= 1'b0;
            input_beat_count  <= 2'b0;
        end else begin
            if (input_axis_tvalid && input_axis_tready)
                input_axis_tvalid <= 1'b0;

            if (input_valid && input_ready) begin
                case (input_beat_count)
                    2'd0: input_axis_tdata[127:0]   <= input_data;
                    2'd1: input_axis_tdata[255:128] <= input_data;
                    2'd2: input_axis_tdata[383:256] <= input_data;
                    2'd3: begin
                        input_axis_tdata[511:384] <= input_data;
                        input_axis_tvalid <= 1'b1;
                    end
                endcase
                input_beat_count <= input_beat_count + 1'b1;
            end
        end
    end

    // Convert ap_fixed<23,13> to the existing ap_fixed<22,11> score format.
    // Both formats use a zero-padded 32-bit AXI container.
    assign output_compat_tdata = {output_axis_tdata[20:0], 1'b0};
    assign output_data       = {{(OUTPUT_WIDTH-22){1'b0}}, output_compat_tdata};
    assign output_valid      = output_axis_tvalid;
    assign output_axis_tready = output_ready;

    assign ap_start = start;
    assign done  = ap_done;
    assign idle  = ap_idle;
    assign ready = ap_ready;

    // CNN Core Instance (direct RTL instantiation, replaces Vivado IP cnn_core_0)
    cnn_core cnn_core_inst (
        .ap_clk              (clk),
        .ap_rst_n            (rst_n),
        .ap_start            (ap_start),
        .ap_done             (ap_done),
        .ap_idle             (ap_idle),
        .ap_ready            (ap_ready),
        .waveform_TDATA      (input_axis_tdata),
        .waveform_TVALID     (input_axis_tvalid),
        .waveform_TREADY     (input_axis_tready),
        .layer9_out_TDATA    (output_axis_tdata),
        .layer9_out_TVALID   (output_axis_tvalid),
        .layer9_out_TREADY   (output_axis_tready)
    );

endmodule
