################################################################################
# Pin Constraints for CNN4HW_TOP (1D CNN)
# Target Device: xcku5p-ffvb676-2-e
# Date: 2025/11/07
################################################################################

################################################################################
# Clock and Reset Pins
################################################################################

# System Clock (200 MHz recommended)
set_property PACKAGE_PIN E13 [get_ports clk]

# Active-Low Reset
set_property PACKAGE_PIN H11 [get_ports rst_n]


################################################################################
# Control Interface Pins
################################################################################

# Start Signal (pulse to start inference)
set_property PACKAGE_PIN G11 [get_ports start]

# Done Signal (inference complete)
set_property PACKAGE_PIN J14 [get_ports done]

# Idle Signal (IP is idle)
set_property PACKAGE_PIN H14 [get_ports idle]

# Ready Signal (IP ready for data)
set_property PACKAGE_PIN H13 [get_ports ready]


################################################################################
# Input Data Interface - 64-bit (4 channels x 16 bits)
# Format: {ch3[15:0], ch2[15:0], ch1[15:0], ch0[15:0]}
################################################################################

# Input Data Bus [63:0] - 64-bit parallel input
# Channel 0 [15:0]  (HD Bank 86)  -- 已填
set_property PACKAGE_PIN C11 [get_ports {input_data[0]}]
set_property PACKAGE_PIN B11 [get_ports {input_data[1]}]
set_property PACKAGE_PIN B10 [get_ports {input_data[2]}]
set_property PACKAGE_PIN A10 [get_ports {input_data[3]}]
set_property PACKAGE_PIN B9  [get_ports {input_data[4]}]
set_property PACKAGE_PIN A9  [get_ports {input_data[5]}]
set_property PACKAGE_PIN D9  [get_ports {input_data[6]}]
set_property PACKAGE_PIN C9  [get_ports {input_data[7]}]
set_property PACKAGE_PIN D11 [get_ports {input_data[8]}]
set_property PACKAGE_PIN D10 [get_ports {input_data[9]}]
set_property PACKAGE_PIN E11 [get_ports {input_data[10]}]
set_property PACKAGE_PIN E10 [get_ports {input_data[11]}]
set_property PACKAGE_PIN F10 [get_ports {input_data[12]}]
set_property PACKAGE_PIN F9  [get_ports {input_data[13]}]
set_property PACKAGE_PIN G10 [get_ports {input_data[14]}]
set_property PACKAGE_PIN G9  [get_ports {input_data[15]}]

# Channel 1 [31:16]  (HD Bank 84)  -- 新增
set_property PACKAGE_PIN W12  [get_ports {input_data[16]}]
set_property PACKAGE_PIN W13  [get_ports {input_data[17]}]
set_property PACKAGE_PIN Y13  [get_ports {input_data[18]}]
set_property PACKAGE_PIN AA13 [get_ports {input_data[19]}]
set_property PACKAGE_PIN W14  [get_ports {input_data[20]}]
set_property PACKAGE_PIN W15  [get_ports {input_data[21]}]
set_property PACKAGE_PIN W16  [get_ports {input_data[22]}]
set_property PACKAGE_PIN Y16  [get_ports {input_data[23]}]
set_property PACKAGE_PIN AA14 [get_ports {input_data[24]}]
set_property PACKAGE_PIN AB14 [get_ports {input_data[25]}]
set_property PACKAGE_PIN AA15 [get_ports {input_data[26]}]
set_property PACKAGE_PIN Y15  [get_ports {input_data[27]}]
set_property PACKAGE_PIN AB15 [get_ports {input_data[28]}]
set_property PACKAGE_PIN AB16 [get_ports {input_data[29]}]
set_property PACKAGE_PIN AC13 [get_ports {input_data[30]}]
set_property PACKAGE_PIN AC14 [get_ports {input_data[31]}]

# Channel 2 [47:32]  (HP Bank 65)  -- 新增
set_property PACKAGE_PIN N21 [get_ports {input_data[32]}]
set_property PACKAGE_PIN N22 [get_ports {input_data[33]}]
set_property PACKAGE_PIN P21 [get_ports {input_data[34]}]
set_property PACKAGE_PIN R21 [get_ports {input_data[35]}]
set_property PACKAGE_PIN R20 [get_ports {input_data[36]}]
set_property PACKAGE_PIN P20 [get_ports {input_data[37]}]
set_property PACKAGE_PIN P19 [get_ports {input_data[38]}]
set_property PACKAGE_PIN N19 [get_ports {input_data[39]}]
set_property PACKAGE_PIN N23 [get_ports {input_data[40]}]
set_property PACKAGE_PIN P23 [get_ports {input_data[41]}]
set_property PACKAGE_PIN R23 [get_ports {input_data[42]}]
set_property PACKAGE_PIN R22 [get_ports {input_data[43]}]
set_property PACKAGE_PIN T19 [get_ports {input_data[44]}]
set_property PACKAGE_PIN N26 [get_ports {input_data[45]}]
set_property PACKAGE_PIN R26 [get_ports {input_data[46]}]
set_property PACKAGE_PIN R25 [get_ports {input_data[47]}]

# Channel 3 [63:48]  (HP Bank 66)  -- 新增
set_property PACKAGE_PIN B26 [get_ports {input_data[48]}]
set_property PACKAGE_PIN B25 [get_ports {input_data[49]}]
set_property PACKAGE_PIN C26 [get_ports {input_data[50]}]
set_property PACKAGE_PIN D26 [get_ports {input_data[51]}]
set_property PACKAGE_PIN C24 [get_ports {input_data[52]}]
set_property PACKAGE_PIN D23 [get_ports {input_data[53]}]
set_property PACKAGE_PIN D25 [get_ports {input_data[54]}]
set_property PACKAGE_PIN D24 [get_ports {input_data[55]}]
set_property PACKAGE_PIN E23 [get_ports {input_data[56]}]
set_property PACKAGE_PIN F23 [get_ports {input_data[57]}]
set_property PACKAGE_PIN E26 [get_ports {input_data[58]}]
set_property PACKAGE_PIN E25 [get_ports {input_data[59]}]
set_property PACKAGE_PIN F22 [get_ports {input_data[60]}]
set_property PACKAGE_PIN G22 [get_ports {input_data[61]}]
set_property PACKAGE_PIN H22 [get_ports {input_data[62]}]
set_property PACKAGE_PIN H21 [get_ports {input_data[63]}]

# Input Valid Signal
set_property PACKAGE_PIN J12 [get_ports input_valid]

# Input Ready Signal (output from FPGA)
set_property PACKAGE_PIN G14 [get_ports input_ready]


################################################################################
# Output Data Interface - 16-bit
################################################################################

# Output Data Bus [15:0] - 16-bit result  (HD Bank 87)
set_property PACKAGE_PIN B14 [get_ports {output_data[0]}]
set_property PACKAGE_PIN A14 [get_ports {output_data[1]}]
set_property PACKAGE_PIN A13 [get_ports {output_data[2]}]
set_property PACKAGE_PIN A12 [get_ports {output_data[3]}]
set_property PACKAGE_PIN C12 [get_ports {output_data[4]}]
set_property PACKAGE_PIN B12 [get_ports {output_data[5]}]
set_property PACKAGE_PIN C14 [get_ports {output_data[6]}]
set_property PACKAGE_PIN C13 [get_ports {output_data[7]}]
set_property PACKAGE_PIN D14 [get_ports {output_data[8]}]
set_property PACKAGE_PIN D13 [get_ports {output_data[9]}]
set_property PACKAGE_PIN E12 [get_ports {output_data[10]}]
set_property PACKAGE_PIN F14 [get_ports {output_data[11]}]
set_property PACKAGE_PIN F13 [get_ports {output_data[12]}]
set_property PACKAGE_PIN G12 [get_ports {output_data[13]}]
set_property PACKAGE_PIN F12 [get_ports {output_data[14]}]
set_property PACKAGE_PIN J15 [get_ports {output_data[15]}]

# Output Valid Signal
set_property PACKAGE_PIN J13 [get_ports output_valid]

# Output Ready Signal (input to FPGA)
set_property PACKAGE_PIN H12 [get_ports output_ready]