`timescale 1ns / 10ps
//////////////////////////////////////////////////////////////////////////////////
// Company: University of California, Irvine
// Engineer: Albert L. Cheung
// 
// Create Date: 02/11/2026 04:50:39 PM
// Design Name: CNN Core Wrapper
// Module Name: tb_stream
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

module tb_WRAPPER_TOP;

    parameter CLK_PERIOD    = 5.0; 
    parameter NUM_TIMESTEPS = 256;
    parameter NUM_CHANNELS  = 4;
    parameter INPUT_WIDTH   = 64;
    parameter OUTPUT_WIDTH  = 32;

    parameter NUM_SAMPLES     = 1000;
    parameter START_SAMPLE_ID = 0;
    parameter TIMEOUT_CYCLES  = 50000000;

    // Signals
    reg clk, rst_n, start;
    wire done, idle, ready;
    reg  [INPUT_WIDTH-1:0] input_data;
    reg  input_valid;
    wire input_ready;
    wire [OUTPUT_WIDTH-1:0] output_data;
    wire output_valid;
    reg  output_ready;

    // Variables
    reg [1023:0] output_csv_path;
    integer csv_file;
    reg [63:0] start_time_fifo [0:2047];
    integer fifo_head = 0, fifo_tail = 0;
    integer sent_count = 0, received_count = 0;
    reg [63:0] current_sample_packed [0:NUM_TIMESTEPS-1]; 
    real total_latency_acc = 0;
    reg [63:0] sim_start_time, sim_end_time;
    integer correct_count = 0;


    reg [31:0] labels [0:NUM_SAMPLES-1];


    WRAPPER_TOP #(
        .INPUT_WIDTH(INPUT_WIDTH),
        .OUTPUT_WIDTH(OUTPUT_WIDTH),
        .NUM_TIMESTEPS(NUM_TIMESTEPS),
        .NUM_CHANNELS(NUM_CHANNELS)
    ) uut (
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

    // Clock
    initial clk = 0;
    always #(CLK_PERIOD/2.0) clk = ~clk;

    // Main
    initial begin
        output_csv_path = "out/sim_out/inference_results_stream.csv";
        csv_file = $fopen(output_csv_path, "w");
        if (csv_file == 0) begin
            $display("[ERROR] Cannot open CSV."); $finish;
        end
        $fwrite(csv_file, "sample_id,hex_out,float_out,label,prediction,correct,latency_cycles,latency_us\n");

        $readmemh("data/testhex_stream/labels.hex", labels);

        rst_n = 0; start = 0; input_valid = 0; output_ready = 1;
        input_data = 64'h0;

        $display("[%0t] Asserting Reset...", $time);
        repeat(20) @(posedge clk);
        rst_n = 1;
        repeat(10) @(posedge clk);
        $display("[%0t] Starting Pipelined Test for vanilla_stream_prj...", $time);
        $display("[%0t] Input: %0d-bit, Output: %0d-bit", $time, INPUT_WIDTH, OUTPUT_WIDTH);

        sim_start_time = $time;

        fork
            input_driver_thread();
            output_monitor_thread();
        join

        sim_end_time = $time;
        print_summary();
        $fclose(csv_file);
        $finish;
    end

    // Input Task
    task input_driver_thread;
        integer s_id, t;
        reg [1023:0] filename;
        begin
            for (s_id = START_SAMPLE_ID; s_id < START_SAMPLE_ID + NUM_SAMPLES; s_id = s_id + 1) begin
                $sformat(filename, "data/testhex_stream/test_input_sample%0d.hex", s_id);
                $readmemh(filename, current_sample_packed);

                if (current_sample_packed[0] === 64'bx) begin
                    $display("[ERROR] Failed to load sample %0d.", s_id); $finish;
                end

                while (!idle && !ready) @(posedge clk);
                start <= 1;
                start_time_fifo[fifo_tail] = $time;
                fifo_tail = (fifo_tail + 1) % 2048;
                input_valid <= 1;

                for (t = 0; t < NUM_TIMESTEPS; t = t + 1) begin
                    input_data <= current_sample_packed[t];
                    @(posedge clk);
                    while (!input_ready) begin
                         @(posedge clk);
                         if (ready && start) start <= 0;
                    end
                    if (ready && start) start <= 0;
                end
                input_valid <= 0;
                sent_count = sent_count + 1;
                if (start) begin
                    while (!ready) @(posedge clk);
                    start <= 0;
                end
            end
        end
    endtask

    // Output Task
    task output_monitor_thread;
        integer latency_cycles;
        reg [63:0] t_start, t_end;
        real out_float;
        integer prediction, label_val, is_correct;
        begin
            $display("\n--------------------------------------------------------------------------------");
            $display("Sample_ID | Output_Hex | Output_Float | Label | Pred | Correct | Latency_us");
            $display("--------------------------------------------------------------------------------");

            while (received_count < NUM_SAMPLES) begin
                @(posedge clk);
                if (output_valid && output_ready) begin
                    t_end = $time;
                    if (fifo_head != fifo_tail) begin
                        t_start = start_time_fifo[fifo_head];
                        fifo_head = (fifo_head + 1) % 2048;
                    end else t_start = t_end;

                    latency_cycles = (t_end - t_start) / CLK_PERIOD;

                    out_float = $itor($signed(output_data[16:0])) / 256.0;

                    prediction = (out_float > 0.5) ? 1 : 0;
                    label_val = labels[START_SAMPLE_ID + received_count];
                    is_correct = (prediction == label_val) ? 1 : 0;
                    if (is_correct) correct_count = correct_count + 1;

                    total_latency_acc = total_latency_acc + latency_cycles;

                    $display("%9d | 0x%08h     | %12.6f |   %0d   |  %0d   |    %0d    | %10.2f",
                             (START_SAMPLE_ID + received_count),
                             output_data, out_float, label_val, prediction, is_correct,
                             (latency_cycles * CLK_PERIOD / 1000.0));

                    $fwrite(csv_file, "%0d,0x%08h,%.6f,%0d,%0d,%0d,%0d,%.3f\n",
                            (START_SAMPLE_ID + received_count), output_data, out_float,
                            label_val, prediction, is_correct,
                            latency_cycles, (latency_cycles * CLK_PERIOD / 1000.0));

                    output_ready <= 0;
                    @(posedge clk);
                    output_ready <= 1;
                    received_count = received_count + 1;
                end
            end
        end
    endtask

    task print_summary;
        real avg_latency, total_time_us, throughput, accuracy;
        begin
            $display("\n================================================================================");
            $display("                         SIMULATION SUMMARY");
            $display("================================================================================");
            $display("IP Core:             cnn_core_0");
            $display("Input Interface:     %0d-bit AXI-Stream (4 x ap_fixed<12,6>)", INPUT_WIDTH);
            $display("Output Interface:    %0d-bit AXI-Stream (1 x ap_fixed<17,9>)", OUTPUT_WIDTH);
            $display("Clock Period:        %.2f ns (%.0f MHz)", CLK_PERIOD, 1000.0/CLK_PERIOD);
            $display("--------------------------------------------------------------------------------");
            $display("Samples Sent:        %0d", sent_count);
            $display("Samples Received:    %0d", received_count);
            $display("Correct Predictions: %0d / %0d", correct_count, received_count);

            if (received_count > 0) begin
                accuracy = 100.0 * correct_count / received_count;
                avg_latency = total_latency_acc / received_count;
                total_time_us = (sim_end_time - sim_start_time) / 1000.0;
                throughput = received_count / (total_time_us / 1000000.0);

                $display("Accuracy:            %.2f%%", accuracy);
                $display("--------------------------------------------------------------------------------");
                $display("Average Latency:     %.2f cycles (%.3f us)", avg_latency, avg_latency * CLK_PERIOD / 1000.0);
                $display("Total Time:          %.3f us", total_time_us);
                $display("Throughput:          %.2f samples/sec", throughput);
            end
            $display("================================================================================");
            $display("Results saved to: %s", output_csv_path);
            $display("Simulation Complete.");
        end
    endtask

    // Watchdog
    initial begin
        repeat(TIMEOUT_CYCLES) @(posedge clk);
        if (received_count < NUM_SAMPLES) begin
            $display("\n[ERROR] Watchdog Timeout! Received %0d/%0d samples", received_count, NUM_SAMPLES);
            print_summary();
            $finish;
        end
    end
endmodule
