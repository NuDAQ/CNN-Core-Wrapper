################################################################################
# File: 01_clocks.xdc
# Purpose: Define primary clocks (must load before any delay constraints)
################################################################################

# Timing
create_clock -period 8.000 -name sys_clk [get_ports clk]
