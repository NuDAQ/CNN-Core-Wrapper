# Standalone internal-module budget; not a board or system timing contract.
create_clock -name cnn_clk -period 5.000 [get_ports clk]
set_input_delay -clock cnn_clk -max 1.000 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_input_delay -clock cnn_clk -min 0.000 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_output_delay -clock cnn_clk -max 1.000 [all_outputs]
set_output_delay -clock cnn_clk -min 0.000 [all_outputs]
# Model a concrete clock-buffer source for this standalone OOC budget.
set_property HD.CLK_SRC BUFGCE_X0Y0 [get_ports clk]
