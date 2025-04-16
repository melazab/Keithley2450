# Keithley 2450 SourceMeter Control

This repository contains Python modules for controlling the Keithley 2450 SourceMeter (SMU) to deliver current and measure voltage or vice versa.

## Overview

The `Keithley2450Driver.py` module provides functions to configure the SMU and control source and measurement parameters, including:

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

**Important:** To run `CIC_Keithley2450.py`, make sure to:

1. Activate the Python virtual environment with the necessary dependencies
   `source ./venv/bin/activate` on Linux
2. Configure the SMU to communicate using TSP (SCPI is the default setting on the Keithley 2450).

To change the command set:

1. Access the menu settings on the Keithley 2450
2. Change from SCPI to TSP command set
3. Apply the changes

If the SMU is not properly configured, it won't understand the messages sent by the computer and will likely generate a VISAIOERROR reporting a timeout.

## To-Do List

- Implement the zero-crossing method to:

1. Monitor the rate of change of measured voltage over time
2. Stop sourcing current once dV/dt falls below a predefined threshold.
