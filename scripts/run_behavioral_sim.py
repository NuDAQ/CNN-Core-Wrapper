#!/usr/bin/env python3
"""Compatibility command for the native Verilator behavioral verifier.

For Vivado physical qualification use run_ooc.py. The historical ADC/CSV
conversion flow is replaced by raw native words and exact result counts.
"""
from run_verilator_tests import main

if __name__ == "__main__":
    main()
