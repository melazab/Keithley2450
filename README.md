# Keithley 2450 SourceMeter Control

This repository contains Python modules for controlling the Keithley 2450 SourceMeter (SMU) to deliver current and measure voltage or vice versa.

## Overview

The `Keithley2450Driver.py` module provides functions to configure the SMU and control source and measurement parameters, including:

- `SMU_config` - Configure basic SMU settings

## Charge Injection Capacity Testing

The `CIC_Keithley2450.py` script programs the SMU to source controlled current pulses and measure the resulting voltage

1. Set the measurement to 4-wire configuration
2. Set the SMU to measure current
3. Use the High Z output off state
4. Set the SMU to source current (eg. -1 mA, -2 mA, -4 mA, etc...)
5. Turn on the current source readback function
6. Set the voltage limit (compliance) to the desired charge/discharge level (Max = 210V)
7. Read back the current, source readback voltage, and relative timestamp
8. Monitor the voltage until the battery reaches the desired level and stop the test

## Setup Requirements

**Important:** To execute the `cyclingTestKeithley2450.py` code, the SMU must be in the TSP command set mode (SCPI command is the default setting on the Keithley 2450).

To change the command set:
1. Access the menu settings on the SMU
2. Change from SCPI to TSP command set
3. Apply the changes

If the SMU is not properly configured, it won't understand the messages sent by the computer and will likely generate a VISAIOERROR reporting a timeout.

## To-Do List

- Implement the zero-crossing method to stop sourcing current once dV/dt 
