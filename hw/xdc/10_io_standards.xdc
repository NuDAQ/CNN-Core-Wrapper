################################################################################
# File: 10_io_standards.xdc
# Purpose: I/O standards (voltage levels) for ports, grouped by IO Bank
# Assumption: Banks 65/66/86/87/84 are at 1.8 V (LVCMOS18). 
# NOTE: If your board powers Bank 84 at 2.5 V or 3.3 V, change Bank 84 section
#       from LVCMOS18 to LVCMOS25 or LVCMOS33 accordingly.
################################################################################

# ===== Common control / handshake / clock =====
# Bank87: clk, done, idle, ready, input_valid, input_ready, output_data[*], output_valid, output_ready
set_property IOSTANDARD LVCMOS18 [get_ports clk]
set_property IOSTANDARD LVCMOS18 [get_ports {done idle ready}]
set_property IOSTANDARD LVCMOS18 [get_ports {input_valid input_ready}]
set_property IOSTANDARD LVCMOS18 [get_ports {output_valid output_ready}]
set_property IOSTANDARD LVCMOS18 [get_ports {output_data[*]}]

# Bank86: rst_n, start (你的分配里 G11/H11 落在 86)
set_property IOSTANDARD LVCMOS18 [get_ports {rst_n start}]

# ===== Input data bus by channel/bank =====
# CH0 [15:0]  -> Bank86
set_property IOSTANDARD LVCMOS18 [get_ports { \
  input_data[0]  input_data[1]  input_data[2]  input_data[3]  \
  input_data[4]  input_data[5]  input_data[6]  input_data[7]  \
  input_data[8]  input_data[9]  input_data[10] input_data[11] \
  input_data[12] input_data[13] input_data[14] input_data[15] }]

# CH1 [31:16] -> Bank84  (如 VCCO_84 ≠ 1.8 V，请改成 LVCMOS25/33)
set_property IOSTANDARD LVCMOS18 [get_ports { \
  input_data[16] input_data[17] input_data[18] input_data[19] \
  input_data[20] input_data[21] input_data[22] input_data[23] \
  input_data[24] input_data[25] input_data[26] input_data[27] \
  input_data[28] input_data[29] input_data[30] input_data[31] }]

# CH2 [47:32] -> Bank65 (HP, 1.8 V)
set_property IOSTANDARD LVCMOS18 [get_ports { \
  input_data[32] input_data[33] input_data[34] input_data[35] \
  input_data[36] input_data[37] input_data[38] input_data[39] \
  input_data[40] input_data[41] input_data[42] input_data[43] \
  input_data[44] input_data[45] input_data[46] input_data[47] }]

# CH3 [63:48] -> Bank66 (HP, 1.8 V)
set_property IOSTANDARD LVCMOS18 [get_ports { \
  input_data[48] input_data[49] input_data[50] input_data[51] \
  input_data[52] input_data[53] input_data[54] input_data[55] \
  input_data[56] input_data[57] input_data[58] input_data[59] \
  input_data[60] input_data[61] input_data[62] input_data[63] }]