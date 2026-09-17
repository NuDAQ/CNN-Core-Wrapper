`timescale 1ns/1ps
module tb_native_wrapper;
    localparam MAX_WINDOWS = 2048;
    logic clk = 0;
    always #2.5 clk = ~clk;
    logic rst_n = 0, start = 0, input_valid = 0, output_ready = 0;
    logic [511:0] input_data = 0;
    wire input_ready, output_valid, done, idle, ready;
    wire [31:0] output_data;
    wire ref_ir, ref_ov, ref_done, ref_idle, ref_ready;
    wire [31:0] ref_data;
    logic [511:0] words [0:MAX_WINDOWS*32-1];
    logic [31:0] scores [0:MAX_WINDOWS-1];
    integer windows, sent = 0, received = 0, accepted = 0, completed = 0;

    WRAPPER_TOP dut(.*);
    cnn_core reference_ip (
        .ap_clk(clk), .ap_rst_n(rst_n), .ap_start(start),
        .ap_done(ref_done), .ap_idle(ref_idle), .ap_ready(ref_ready),
        .waveform_TDATA(input_data), .waveform_TVALID(input_valid),
        .waveform_TREADY(ref_ir), .layer12_out_TDATA(ref_data),
        .layer12_out_TVALID(ref_ov), .layer12_out_TREADY(output_ready)
    );

    task automatic check_ports;
        assert ({input_ready,output_valid,done,idle,ready} ===
                {ref_ir,ref_ov,ref_done,ref_idle,ref_ready})
            else $fatal(1, "wrapper changed native handshake/control or added latency");
        if (output_valid)
            assert (output_data === ref_data)
                else $fatal(1, "wrapper changed raw native score bits");
    endtask

    initial begin
        if (!$value$plusargs("WINDOWS=%d", windows) || windows < 1 || windows > MAX_WINDOWS)
            $fatal(1, "invalid WINDOWS");
        $readmemh("input.hex", words, 0, windows*32-1);
        $readmemh("expected.hex", scores, 0, windows-1);
        repeat (5) @(negedge clk);
        rst_n = 1;
        for (integer cycle = 0; cycle < 500000; cycle++) begin
            @(negedge clk);
            start = accepted < windows;
            input_valid = sent < windows*32;
            if (input_valid) input_data = words[sent];
            output_ready = 1;
            #1;
            check_ports();
            @(posedge clk);
            check_ports();
            if (start && ready) accepted++;
            if (done) completed++;
            if (input_valid && input_ready) sent++;
            if (output_valid && output_ready) begin
                if (received >= windows) $fatal(1, "extra result");
                assert (output_data === scores[received])
                    else $fatal(1, "score window=%0d got=%h expected=%h", received, output_data, scores[received]);
                received++;
            end
            if (received == windows && accepted == windows && completed == windows) break;
        end
        assert (sent == windows*32 && received == windows && accepted == windows && completed == windows)
            else $fatal(1, "incomplete run inputs=%0d outputs=%0d starts=%0d done=%0d", sent, received, accepted, completed);
        @(negedge clk);
        input_valid = 0; start = 0;
        repeat (100) begin
            @(posedge clk);
            check_ports();
            assert (!output_valid && !done) else $fatal(1, "extra transaction after stop");
        end
        assert (idle) else $fatal(1, "IP not idle after all transactions");
        $display("PASS native windows=%0d inputs=%0d outputs=%0d starts=%0d done=%0d", windows, sent, received, accepted, completed);
        $finish;
    end
endmodule
