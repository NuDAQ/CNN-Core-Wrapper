# Standalone internal-module budget; not a board or system timing contract.
create_clock -name cnn_clk -period 5.000 [get_ports clk]
set sync_inputs [remove_from_collection [all_inputs] [get_ports clk]]
set_input_delay -clock cnn_clk -max 1.000 $sync_inputs
set_input_delay -clock cnn_clk -min 0.000 $sync_inputs
set_output_delay -clock cnn_clk -max 1.000 [all_outputs]
set_output_delay -clock cnn_clk -min 0.000 [all_outputs]
