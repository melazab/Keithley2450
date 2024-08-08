This document describes how to use the Keithley 2450 
SourceMeter (SMU) for performing charge and discharge
cycle testing to evaluate the charge capacity of slurry
electrodes.

cyclingTestKeithley2450.py programs the SMU to perform the
following steps:
1 - Set the measurement to 4-wire configuration.
2 - Set the SMU to measure current.
3 - Use the High Z output off state.
4 - Set the SMU to source voltage.
5 - Turn on the voltage source readback function.
6 - Set the current limit (or compliance) to the current level at which the battery is to be charged or discharged.
7 - Read back the load current, source readback voltage and the relative timestamp.
8 - Monitor the voltage until the battery reaches the desired voltage level and stop the test.


* To execute the cyclingTestKeithley2450.py code, the SMU must be in the TSP command set
mode (SCPI command is the default). Go in the menu settings to change that command set
if necessary. If you don't configure the SMU, it won't understand the messages sent by the
computer and will likely see a VISAIOERROR reporting a timeout.
