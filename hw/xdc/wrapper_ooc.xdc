# Qualification-only common-clock fixture; never import into a system build.
create_clock -name cnn_clk -period 5.000 [get_ports clk]
set fixture_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_input_delay -clock cnn_clk -max 1.000 $fixture_inputs
set_input_delay -clock cnn_clk -min 0.000 $fixture_inputs
set_output_delay -clock cnn_clk -max 1.000 [all_outputs]
set_output_delay -clock cnn_clk -min 0.000 [all_outputs]

set launch_cells [get_cells -hierarchical -filter {NAME =~ launch_* && IS_SEQUENTIAL}]
set capture_cells [get_cells -hierarchical -filter {NAME =~ capture_* && IS_SEQUENTIAL}]
# The fixture's external pins are outside the qualified register-to-register DUT.
# These exceptions stop at fixture registers and never cut a path through the DUT.
set_false_path -from $fixture_inputs -to $launch_cells
set_false_path -from $capture_cells -to [all_outputs]
# Reserve 1 ns at the DUT boundary; retain normal clock skew and hold analysis.
set_max_delay 4.000 -from $launch_cells
set_max_delay 4.000 -to $capture_cells
