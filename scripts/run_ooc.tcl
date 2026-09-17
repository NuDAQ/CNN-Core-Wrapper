# Run from the portable directory prepared by run_ooc.py.
proc write_text {path text} {
    set fp [open $path w]
    puts $fp $text
    close $fp
}

if {[catch {
    file delete -force result.json
    set_param general.maxThreads 4
    file mkdir reports
    create_project -in_memory -part xcku5p-ffvb676-2-e
    read_verilog [lsort [glob rtl/*.v]]
    read_xdc ooc.xdc
    synth_design -top WRAPPER_OOC -part xcku5p-ffvb676-2-e -mode out_of_context
    set launch_cells [get_cells -hierarchical -filter {NAME =~ launch_* && IS_SEQUENTIAL}]
    set capture_cells [get_cells -hierarchical -filter {NAME =~ capture_* && IS_SEQUENTIAL}]
    if {[llength $launch_cells] != 516 || [llength $capture_cells] != 37} {
        error "Missing fixture registers: launch=[llength $launch_cells], capture=[llength $capture_cells]"
    }
    if {[llength [get_cells u_wrapper]] != 1} {error "Missing wrapper hierarchy"}
    report_utilization -file reports/post_synth_utilization.rpt
    opt_design
    place_design
    phys_opt_design
    route_design
    write_checkpoint -force routed.dcp
    report_utilization -file reports/utilization.rpt
    report_utilization -hierarchical -file reports/utilization_hierarchical.rpt
    report_route_status -file reports/route_status.rpt
    report_drc -file reports/drc.rpt
    report_methodology -file reports/methodology.rpt
    report_exceptions -file reports/exceptions.rpt
    report_timing_summary -delay_type min_max -check_timing_verbose -report_unconstrained -file reports/timing_summary.rpt
    # Prove both boundary budgets exist and produce actual timed paths.
    foreach direction {launch capture} {
        if {$direction eq "launch"} {
            set paths [get_timing_paths -from $launch_cells -max_paths 1]
            report_timing -from $launch_cells -delay_type min_max -max_paths 10 -file reports/launch_boundary.rpt
        } else {
            set paths [get_timing_paths -to $capture_cells -max_paths 1]
            report_timing -to $capture_cells -delay_type min_max -max_paths 10 -file reports/capture_boundary.rpt
        }
        if {[llength $paths] != 1 || abs([get_property REQUIREMENT $paths] - 4.0) > 0.001} {
            error "Missing or incorrect 4 ns $direction boundary budget"
        }
    }
    set fp [open reports/timing_summary.rpt r]
    set timing [read $fp]
    close $fp

    # Fail closed if any timing metric or required coverage check is absent.
    set columns 0
    set metrics {}
    foreach line [split $timing "\n"] {
        if {[string first "WNS(ns)" $line] >= 0 && [string first "WPWS(ns)" $line] >= 0} {
            set columns 1
            continue
        }
        if {$columns} {
            set values [regexp -all -inline {[-+]?[0-9]+[.]?[0-9]*} $line]
            if {[llength $values] == 12} {
                set metrics [list [lindex $values 0] [lindex $values 4] [lindex $values 8]]
                break
            }
        }
    }
    if {[llength $metrics] != 3} {error "Missing setup/hold/pulse-width metrics"}
    foreach value $metrics {
        if {$value < 0.0} {error "Timing violation: WNS/WHS/WPWS=$metrics"}
    }
    foreach check {no_clock unconstrained_internal_endpoints no_input_delay no_output_delay partial_input_delay partial_output_delay} {
        set pattern [format {checking %s \(([0-9]+)\)} $check]
        if {![regexp -nocase $pattern $timing unused count] || $count != 0} {
            error "Missing or failing timing coverage check: $check"
        }
    }
    set incomplete [get_nets -hierarchical -filter {ROUTE_STATUS == UNROUTED || ROUTE_STATUS == PARTIAL}]
    if {[llength $incomplete] != 0} {error "Incomplete routing: [llength $incomplete] nets"}
    set blocking [get_drc_violations -filter {SEVERITY == Error || SEVERITY == {Critical Warning}}]
    if {[llength $blocking] != 0} {error "Blocking DRC violations: $blocking"}
    lassign $metrics wns whs wpws
    write_text result.json [format {"status":"passed","part":"xcku5p-ffvb676-2-e","top":"WRAPPER_OOC","period_ns":5.0,"boundary_max_ns":4.0,"wns_ns":%s,"whs_ns":%s,"wpws_ns":%s,"vivado":"%s"} $wns $whs $wpws [version -short]]
    # Add the outer JSON object without Tcl interpreting JSON brackets.
    set fp [open result.json r]; set result [read $fp]; close $fp
    write_text result.json "\{$result\}"
    puts "PASS: native wrapper routed OOC timing $metrics"
} message options]} {
    puts stderr "ERROR: $message"
    if {[dict exists $options -errorinfo]} {puts stderr [dict get $options -errorinfo]}
    exit 1
}
exit 0
