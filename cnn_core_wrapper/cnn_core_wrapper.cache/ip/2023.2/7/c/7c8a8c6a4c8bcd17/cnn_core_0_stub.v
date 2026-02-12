// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.
// --------------------------------------------------------------------------------
// Tool Version: Vivado v.2023.2 (lin64) Build 4029153 Fri Oct 13 20:13:54 MDT 2023
// Date        : Wed Feb 11 18:12:00 2026
// Host        : AlbertsUbuntu running 64-bit Ubuntu 22.04.5 LTS
// Command     : write_verilog -force -mode synth_stub -rename_top decalper_eb_ot_sdeen_pot_pi_dehcac_xnilix -prefix
//               decalper_eb_ot_sdeen_pot_pi_dehcac_xnilix_ cnn_core_0_stub.v
// Design      : cnn_core_0
// Purpose     : Stub declaration of top-level module interface
// Device      : xcku5p-ffvb676-2-e
// --------------------------------------------------------------------------------

// This empty module with port declaration file causes synthesis tools to infer a black box for IP.
// The synthesis directives are for Synopsys Synplify support to prevent IO buffer insertion.
// Please paste the declaration into a Verilog source file or add the file as an additional source.
(* X_CORE_INFO = "cnn_core,Vivado 2023.2" *)
module decalper_eb_ot_sdeen_pot_pi_dehcac_xnilix(input_layer_TVALID, input_layer_TREADY, 
  input_layer_TDATA, layer10_out_TVALID, layer10_out_TREADY, layer10_out_TDATA, ap_clk, 
  ap_rst_n, ap_start, ap_done, ap_ready, ap_idle)
/* synthesis syn_black_box black_box_pad_pin="input_layer_TVALID,input_layer_TREADY,input_layer_TDATA[63:0],layer10_out_TVALID,layer10_out_TREADY,layer10_out_TDATA[31:0],ap_rst_n,ap_start,ap_done,ap_ready,ap_idle" */
/* synthesis syn_force_seq_prim="ap_clk" */;
  input input_layer_TVALID;
  output input_layer_TREADY;
  input [63:0]input_layer_TDATA;
  output layer10_out_TVALID;
  input layer10_out_TREADY;
  output [31:0]layer10_out_TDATA;
  input ap_clk /* synthesis syn_isclock = 1 */;
  input ap_rst_n;
  input ap_start;
  output ap_done;
  output ap_ready;
  output ap_idle;
endmodule
