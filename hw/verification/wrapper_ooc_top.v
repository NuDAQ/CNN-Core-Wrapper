`timescale 1ns / 1ps

// Physical qualification fixture only. This is not a streaming adapter.
// Common-clock registers provide real launch/capture endpoints around the DUT.
module WRAPPER_OOC (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire [511:0] input_data,
    input wire input_valid,
    input wire output_ready,
    output reg done,
    output reg idle,
    output reg ready,
    output reg input_ready,
    output reg [31:0] output_data,
    output reg output_valid
);
    wire qual_clk;
    BUFG clock_buffer (.I(clk), .O(qual_clk));

    (* DONT_TOUCH = "yes" *) reg launch_rst_n, launch_start;
    (* DONT_TOUCH = "yes" *) reg [511:0] launch_data;
    (* DONT_TOUCH = "yes" *) reg launch_valid, launch_output_ready;
    (* DONT_TOUCH = "yes" *) reg capture_done, capture_idle, capture_ready;
    (* DONT_TOUCH = "yes" *) reg capture_input_ready, capture_output_valid;
    (* DONT_TOUCH = "yes" *) reg [31:0] capture_data;
    wire dut_done, dut_idle, dut_ready, dut_input_ready, dut_output_valid;
    wire [31:0] dut_output_data;

    (* KEEP_HIERARCHY = "yes" *) WRAPPER_TOP u_wrapper (
        .clk(qual_clk), .rst_n(launch_rst_n), .start(launch_start),
        .input_data(launch_data), .input_valid(launch_valid),
        .output_ready(launch_output_ready),
        .done(dut_done), .idle(dut_idle), .ready(dut_ready),
        .input_ready(dut_input_ready), .output_data(dut_output_data),
        .output_valid(dut_output_valid)
    );

    always @(posedge qual_clk) begin
        launch_rst_n <= rst_n;
        launch_start <= start;
        launch_data <= input_data;
        launch_valid <= input_valid;
        launch_output_ready <= output_ready;
        capture_done <= dut_done;
        capture_idle <= dut_idle;
        capture_ready <= dut_ready;
        capture_input_ready <= dut_input_ready;
        capture_data <= dut_output_data;
        capture_output_valid <= dut_output_valid;
    end
    always @* begin
        done = capture_done;
        idle = capture_idle;
        ready = capture_ready;
        input_ready = capture_input_ready;
        output_data = capture_data;
        output_valid = capture_output_valid;
    end
endmodule
