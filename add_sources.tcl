# This script was generated automatically by bender.
set ROOT [file normalize [file dirname [info script]]]

# Package(cnn-core) Target(*)
add_files -norecurse -fileset [current_fileset] [list \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_dense_wide_stream_array_array_ap_fixed_1u_config7_Pipeline_DenseWideMain.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_dense_wide_stream_array_array_ap_fixed_9_5_5_3_0_1u_config7_s.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_fifo_w252_d4_S.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_fifo_w448_d4_S.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_first_conv_4lane_temporal_wide_cl_array_array_ap_fixed_28u_config3_s.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_flow_control_loop_pipe.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_flow_control_loop_pipe_sequential_init.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_maxpool2d_wide_nonoverlap_cl_array_array_ap_fixed_28u_config5_s.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_mul_12s_5ns_15_1_1.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_mul_16s_6s_20_1_1.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_regslice_both.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_relu_array_ap_fixed_28u_array_ap_fixed_16_6_5_3_0_28u_relu_config4_s.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_sparsemux_11_3_12_1_1.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_sparsemux_2353_11_6_1_1.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_sparsemux_9_2_16_1_1.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_start_for_dense_wide_stream_array_array_ap_fixed_9_5_5_3_0_1u_config7_U0.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_start_for_maxpool2d_wide_nonoverlap_cl_array_array_ap_fixed_28u_config5_U0.v \
    $ROOT/.bender/git/checkouts/cnn-core-dc8e560574d139d9/hls_streaming/cnn_core_streaming_prj/solution1/impl/verilog/cnn_core_start_for_relu_array_ap_fixed_28u_array_ap_fixed_16_6_5_3_0_28u_relu_config4_U0.v \
]

# Package(cnn-core-wrapper) Target(*)
add_files -norecurse -fileset [current_fileset] [list \
    $ROOT/hw/rtl/cnn_core_wrapper_top.v \
]

# Package(cnn-core-wrapper) Target(all(fpga, synthesis))
add_files -norecurse -fileset [current_fileset] [list \
    $ROOT/hw/xdc/01_clocks.xdc \
    $ROOT/hw/xdc/02_io_delays.xdc \
    $ROOT/hw/xdc/03_clock_groups.xdc \
    $ROOT/hw/xdc/04_uncertainty.xdc \
    $ROOT/hw/xdc/05_multicycle_falsepaths.xdc \
    $ROOT/hw/xdc/10_io_standards.xdc \
    $ROOT/hw/xdc/20_pins.xdc \
    $ROOT/hw/xdc/21_diff_pairs.xdc \
    $ROOT/hw/xdc/22_interface_adc.xdc \
    $ROOT/hw/xdc/23_interface_spi.xdc \
    $ROOT/hw/xdc/24_interface_axi.xdc \
    $ROOT/hw/xdc/30_timing_extras.xdc \
    $ROOT/hw/xdc/40_debug_ila.xdc \
    $ROOT/hw/xdc/50_power_thermal.xdc \
    $ROOT/hw/xdc/99_local_override.xdc \
]

set_property verilog_define [list \
    TARGET_FPGA \
    TARGET_SYNTHESIS \
    TARGET_VIVADO \
    TARGET_XILINX \
] [current_fileset]

set_property verilog_define [list \
    TARGET_FPGA \
    TARGET_SYNTHESIS \
    TARGET_VIVADO \
    TARGET_XILINX \
] [current_fileset -simset]
