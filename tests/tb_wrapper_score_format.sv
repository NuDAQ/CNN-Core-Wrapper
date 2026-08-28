`timescale 1ns / 1ps

module cnn_core (
    input  wire         ap_clk,
    input  wire         ap_rst_n,
    input  wire         ap_start,
    output wire         ap_done,
    output wire         ap_idle,
    output wire         ap_ready,
    input  wire [511:0] waveform_TDATA,
    input  wire         waveform_TVALID,
    output wire         waveform_TREADY,
    output wire [31:0]  layer9_out_TDATA,
    output wire         layer9_out_TVALID,
    input  wire         layer9_out_TREADY
);
    logic output_valid_r = 1'b0;

    assign waveform_TREADY = 1'b1;
    // Native CNN score: -1.5 in signed ap_fixed<23,13> (10 fractional bits).
    // Vitis zero-extends the 23-bit payload to the 32-bit AXI word.
    assign layer9_out_TDATA = 32'h007ffa00;
    assign layer9_out_TVALID = output_valid_r;
    assign ap_done = output_valid_r && layer9_out_TREADY;
    assign ap_idle = !ap_start;
    assign ap_ready = 1'b1;

    always_ff @(posedge ap_clk) begin
        if (!ap_rst_n) begin
            output_valid_r <= 1'b0;
        end else begin
            if (waveform_TVALID && waveform_TREADY)
                output_valid_r <= 1'b1;
            if (output_valid_r && layer9_out_TREADY)
                output_valid_r <= 1'b0;
        end
    end
endmodule

module tb_wrapper_score_format;
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic start = 1'b0;
    logic [127:0] input_data = '0;
    logic input_valid = 1'b0;
    wire input_ready;
    wire [31:0] output_data;
    wire output_valid;
    logic output_ready = 1'b1;

    wire done;
    wire idle;
    wire ready;

    always #2.5 clk = !clk;

    WRAPPER_TOP dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .done(done),
        .idle(idle),
        .ready(ready),
        .input_data(input_data),
        .input_valid(input_valid),
        .input_ready(input_ready),
        .output_data(output_data),
        .output_valid(output_valid),
        .output_ready(output_ready)
    );

    task automatic send_beat(input logic [127:0] value);
        begin
            @(negedge clk);
            input_data = value;
            input_valid = 1'b1;
            do @(posedge clk); while (!input_ready);
        end
    endtask

    initial begin
        logic saw_output;

        repeat (3) @(posedge clk);
        rst_n = 1'b1;
        start = 1'b1;

        send_beat('0);
        send_beat('0);
        send_beat('0);
        send_beat('0);

        @(negedge clk);
        input_valid = 1'b0;
        start = 1'b0;

        saw_output = 1'b0;
        repeat (10) begin
            @(posedge clk);
            if (output_valid) begin
                // Compatibility score: -1.5 in signed ap_fixed<22,11>,
                // zero-padded like the previous HLS 32-bit AXI container.
                assert (output_data == 32'h003ff400)
                    else $fatal(1, "wrapper did not convert the CNN score to ap_fixed<22,11>");
                saw_output = 1'b1;
            end
        end

        assert (saw_output)
            else $fatal(1, "timed out waiting for wrapper output");
        $display("tb_wrapper_score_format passed");
        $finish;
    end
endmodule
