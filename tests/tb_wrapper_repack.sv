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
    localparam logic [511:0] EXPECTED_WORD = {
        128'h303132333435363738393a3b3c3d3e3f,
        128'h202122232425262728292a2b2c2d2e2f,
        128'h101112131415161718191a1b1c1d1e1f,
        128'h000102030405060708090a0b0c0d0e0f
    };

    logic output_valid_r = 1'b0;

    assign waveform_TREADY = 1'b1;
    assign layer9_out_TDATA = 32'h00000900;
    assign layer9_out_TVALID = output_valid_r;
    assign ap_done = output_valid_r && layer9_out_TREADY;
    assign ap_idle = !ap_start;
    assign ap_ready = 1'b1;

    always_ff @(posedge ap_clk) begin
        if (!ap_rst_n) begin
            output_valid_r <= 1'b0;
        end else begin
            if (waveform_TVALID && waveform_TREADY) begin
                assert (waveform_TDATA == EXPECTED_WORD)
                    else $fatal(1, "wrapper changed the four-beat chronological order");
                output_valid_r <= 1'b1;
            end
            if (output_valid_r && layer9_out_TREADY) begin
                output_valid_r <= 1'b0;
            end
        end
    end
endmodule

module tb_wrapper_repack;
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

        send_beat(128'h000102030405060708090a0b0c0d0e0f);
        send_beat(128'h101112131415161718191a1b1c1d1e1f);
        send_beat(128'h202122232425262728292a2b2c2d2e2f);
        send_beat(128'h303132333435363738393a3b3c3d3e3f);

        @(negedge clk);
        input_valid = 1'b0;
        start = 1'b0;

        saw_output = 1'b0;
        repeat (10) begin
            @(posedge clk);
            if (output_valid) begin
                assert (output_data == 32'h00001200)
                    else $fatal(1, "wrapper changed the CNN result");
                saw_output = 1'b1;
            end
        end

        assert (saw_output)
            else $fatal(1, "timed out waiting for wrapper output");
        $display("tb_wrapper_repack passed");
        $finish;
    end
endmodule
