################################################################################
# File: 02_io_delays.xdc
# Purpose: Input/Output timing relative to sys_clk (requires 01_clocks.xdc)
################################################################################

# Input/Output delay referenced to sys_clk
set_input_delay  -clock sys_clk -max 1.0 [get_ports {input_data[*]}]
set_output_delay -clock sys_clk -max 1.0 [get_ports {output_data[*]}]
