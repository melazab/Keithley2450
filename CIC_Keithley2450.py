#!/usr/bin/env python3

## The pulseWidth parameter in SMU_biphasic_current_pulse
## implies the cathodic and anodic pulses have equal duration

from Keithley2450Driver import SMU_config, SMU_get_measurement, SMU_close, SMU_yyplot, SMU_export_data, fix_time_jumps

from numpy import array, column_stack
from time import time
import matplotlib.pyplot as plt
from pathlib import Path

relativeTimeIn = []
sources = []
measurements = []
cycles = []

def SMU_monophasic_current_pulse(waveformParameters, polarity):
    """ 
    waveformParameters -> Dict that contains the waveform parameters

    polarity -> String that describes whether the current is "anodic" or "cathodic"
    
    """
    if (abs(waveformParameters["currentAmplitude"][polarity]) > 1.05):
        print("Error: SMU_monophasic_current_pulse")
        print("Current Amplitude must be in the range [-1.05, 1.05] A")
        exit
    
    instr = SMU_config("DC_CURRENT", "DC_VOLTAGE", waveformParameters["currentAmplitude"][polarity], waveformParameters["complianceVoltage"])
   
    instr.write("smu.source.output = smu.ON") # Turn on output
    instr.write("timer.cleartime()") # Reset Timer
    tic = time()
    while True:
        elapsed_time, sourceCurrent, measureVoltage = SMU_get_measurement(instr, numDigits = 9)
        relativeTimeIn.append(time() - tic)
        sources.append(sourceCurrent)
        measurements.append(measureVoltage)
        cycles.append(1)

        if elapsed_time > waveformParameters["pulseWidth"][polarity]:
            break
    return instr

def SMU_biphasic_current_pulse(waveformParameters):
    if (waveformParameters["currentAmplitude"]["anodic"] < 0) or (waveformParameters["currentAmplitude"]["anodic"] > 1.05):
        print("Error: SMU_asymmetric_biphasic_current_pulse")
        print("Anodic current amplitude must be in the range [0, 1.05] A")
        exit
    elif (waveformParameters["currentAmplitude"]["cathodic"] < -1.05) or (waveformParameters["currentAmplitude"]["cathodic"] > 0):
        print("Error: SMU_asymmetric_biphasic_current_pulse")
        print("Cathodic current amplitude must be in the range [-1.05, 0] A")
        exit
    
    if waveformParameters["anodicFirst"]:
        instr = SMU_config("DC_CURRENT", "DC_VOLTAGE", waveformParameters["currentAmplitude"]["anodic"], waveformParameters["complianceVoltage"])
    else:
        instr = SMU_config("DC_CURRENT", "DC_VOLTAGE", waveformParameters["currentAmplitude"]["cathodic"], waveformParameters["complianceVoltage"])
    
    instr.write("smu.source.output = smu.ON") # Turn on output
    instr.write("timer.cleartime()") # Reset Timer
    tic = time() # Time 0 of relativeTimeIn array
    while True:
        elapsed_time, sourceCurrent, measureVoltage = SMU_get_measurement(instr, numDigits = 9)
        relativeTimeIn.append(time() - tic)
        sources.append(sourceCurrent)
        measurements.append(measureVoltage)
        cycles.append(1) # only 1 cycle not a train
        if elapsed_time > waveformParameters["pulseWidth"]["anodic"]:
            break
    
    instr.write("timer.cleartime()") # Reset Timer
    if waveformParameters["anodicFirst"]:
        instr.write(f"smu.source.level = {waveformParameters["currentAmplitude"]["cathodic"]}") # Switch from anodic to cathodic
    else: # otherwise if cathodicFirst then switch from cathodic to anodic
        instr.write(f"smu.source.level = {waveformParameters["currentAmplitude"]["anodic"]}")
    while True:
        elapsed_time = SMU_get_measurement(instr, numDigits = 9)
        elapsed_time, sourceCurrent, measureVoltage = SMU_get_measurement(instr, numDigits = 9)
        relativeTimeIn.append(time() - tic)
        sources.append(sourceCurrent)
        measurements.append(measureVoltage)
        cycles.append(1) # only 1 cycle not a train
        if elapsed_time > waveformParameters["pulseWidth"]["cathodic"]:
            break

    instr.write("smu.source.output = smu.OFF")
    return instr

def SMU_monophasic_current_pulse_train(waveformParameters, polarity):
    """ 
    waveformParameters -> Dict that contains the waveform parameters

    polarity -> String that describes whether the current is "anodic" or "cathodic"
    
    """
    if waveformParameters["numPulses"] < 0:
        print("Error: SMU_monophasic_current_pulse_train")
        print("Number of pulses must be non-negative")
        exit

    if (abs(waveformParameters["currentAmplitude"][polarity]) > 1.05):
        print("Error: SMU_monophasic_current_pulse_train")
        print("Current Amplitude must be in the range [-1.05, 1.05] A")
        exit
    
    instr = SMU_config("DC_CURRENT", "DC_VOLTAGE", waveformParameters["currentAmplitude"][polarity], waveformParameters["complianceVoltage"])
    try:
        iter(waveformParameters["pulseWidth"][polarity])
        pulseWidth = waveformParameters["pulseWidth"][polarity]

    except TypeError as te:
        pulseWidth = [waveformParameters["pulseWidth"][polarity] for _ in range(0, waveformParameters["numPulses"])]

    for cycleNumber in range(0, waveformParameters["numPulses"]):
        instr.write("timer.cleartime()") # Reset Timer
        instr.write("smu.source.output = smu.ON") # Turn on output
        elapsed_time = 0
        while (elapsed_time < pulseWidth[cycleNumber]):
            elapsed_time, sourceCurrent, measureVoltage = SMU_get_measurement(instr, numDigits = 9)
            cycles.append(cycleNumber + 1)
            sources.append(sourceCurrent)
            relativeTimeIn.append(elapsed_time)
            measurements.append(measureVoltage)
            
        #instr.write("smu.source.output = smu.OFF") 
        instr.write("smu.source.level = 0")
        while (elapsed_time < pulseWidth[cycleNumber] + waveformParameters["interPulseInterval"]):
            elapsed_time, sourceCurrent, measureVoltage = SMU_get_measurement(instr, numDigits = 9)
            cycles.append(cycleNumber + 1)
            sources.append(sourceCurrent)
            relativeTimeIn.append(elapsed_time)
            measurements.append(measureVoltage)
        instr.write(f"smu.source.level = {waveformParameters["currentAmplitude"][polarity]}")
    return instr

def SMU_biphasic_current_pulse_train(waveformParameters):
    # if waveformParameters["numPulses"] < 0:
    #     print("Error: SMU_biphasic_current_pulse_train")
    #     print("Number of pulses must be non-negative")
    #     exit

    # if (waveformParameters["currentAmplitude"]["anodic"] < 0) or (waveformParameters["currentAmplitude"]["anodic"] > 1.05):
    #     print("Error: SMU_asymmetric_biphasic_current_pulse")
    #     print("Anodic current amplitude must be in the range [0, 1.05] A")
    #     exit
    # elif (waveformParameters["currentAmplitude"]["cathodic"] < -1.05) or (waveformParameters["currentAmplitude"]["cathodic"] > 0):
    #     print("Error: SMU_asymmetric_biphasic_current_pulse")
    #     print("Cathodic current amplitude must be in the range [-1.05, 0] A")
    #     exit
    ## Input Handling ##

    # Handle the case where the pulse width is not constant through out cycles
    # e.g pulse width could be an array [1, 2, 4, 8] which represents a waveform
    # whose pulse width doubles every cycle.

    try:
        iter(waveformParameters["pulseWidth"]["anodic"])
        anodicPulseWidth = waveformParameters["pulseWidth"]["anodic"]
    except TypeError as te:
        anodicPulseWidth = [waveformParameters["pulseWidth"]["anodic"] for _ in range(0, waveformParameters["numPulses"])]

    try:
        iter(waveformParameters["pulseWidth"]["cathodic"])
        cathodicPulseWidth = waveformParameters["pulseWidth"]["cathodic"]
    except TypeError as te:
        cathodicPulseWidth = [waveformParameters["pulseWidth"]["cathodic"] for _ in range(0, waveformParameters["numPulses"])]
    
    # Handle the case where the current amplitude is not constant through out cycles
    # e.g current amplitude could be [1, 2, 4, 8] which represents a waveform whose
    # amplitude doubles every cycle.
    try:
        iter(waveformParameters["currentAmplitude"]["anodic"])
        anodicCurrenAmplitude = waveformParameters["currentAmplitude"]["anodic"]
    except TypeError as te:
        anodicCurrenAmplitude = [waveformParameters["currentAmplitude"]["anodic"] for _ in range(0, waveformParameters["numPulses"])]

    try:
        iter(waveformParameters["currentAmplitude"]["cathodic"])
        cathodicCurrenAmplitude = waveformParameters["currentAmplitude"]["cathodic"]
    except TypeError as te:
        cathodicCurrenAmplitude = [waveformParameters["currentAmplitude"]["cathodic"] for _ in range(0, waveformParameters["numPulses"])]

    if waveformParameters["anodicFirst"]:
        instr = SMU_config("DC_CURRENT", "DC_VOLTAGE",anodicCurrenAmplitude[0] , waveformParameters["complianceVoltage"])
        for cycleNumber in range(0, waveformParameters["numPulses"]):
            instr.write("timer.cleartime()") # Reset Timer
            instr.write("smu.source.level = 0")
            instr.write("smu.source.output = smu.ON") # Turn on output
            elapsed_time = 0
            while (elapsed_time < waveformParameters["interPulseInterval"]):
                elapsed_time, sourceCurrent, measureVoltage = SMU_get_measurement(instr, numDigits = 9)
                cycles.append(cycleNumber + 1)
                sources.append(sourceCurrent)
                relativeTimeIn.append(elapsed_time)
                measurements.append(measureVoltage)
            instr.write(f"smu.source.level = {anodicCurrenAmplitude[cycleNumber]}")
            while (elapsed_time < anodicPulseWidth[cycleNumber] + waveformParameters["interPulseInterval"]):
                elapsed_time, sourceCurrent, measureVoltage = SMU_get_measurement(instr, numDigits = 9)
                cycles.append(cycleNumber + 1)
                sources.append(sourceCurrent)
                relativeTimeIn.append(elapsed_time)
                measurements.append(measureVoltage)
            instr.write(f"smu.source.level = {cathodicCurrenAmplitude[cycleNumber]}")
            while (elapsed_time < anodicPulseWidth[cycleNumber] + cathodicPulseWidth[cycleNumber] + waveformParameters["interPulseInterval"]):
                elapsed_time, sourceCurrent, measureVoltage = SMU_get_measurement(instr, numDigits = 9)
                cycles.append(cycleNumber + 1)
                sources.append(sourceCurrent)
                relativeTimeIn.append(elapsed_time)
                measurements.append(measureVoltage)
            instr.write("smu.source.level = 0")
            while (elapsed_time < anodicPulseWidth[cycleNumber] + cathodicPulseWidth[cycleNumber] + 2 * waveformParameters["interPulseInterval"]):
               elapsed_time, sourceCurrent, measureVoltage = SMU_get_measurement(instr, numDigits = 9)
               cycles.append(cycleNumber + 1)
               sources.append(sourceCurrent)
               relativeTimeIn.append(elapsed_time)
               measurements.append(measureVoltage)
    else:
        instr = SMU_config("DC_CURRENT", "DC_VOLTAGE", cathodicCurrenAmplitude[0], waveformParameters["complianceVoltage"])
        for cycleNumber in range(0, waveformParameters["numPulses"]):
            instr.write("timer.cleartime()") # Reset Timer
            instr.write("smu.source.level = 0")
            instr.write("smu.source.output = smu.ON") # Turn on output
            elapsed_time = 0
            while (elapsed_time < waveformParameters["interPulseInterval"]):
                elapsed_time, sourceCurrent, measureVoltage = SMU_get_measurement(instr, numDigits = 9)
                cycles.append(cycleNumber + 1)
                sources.append(sourceCurrent)
                relativeTimeIn.append(elapsed_time)
                measurements.append(measureVoltage)
            instr.write(f"smu.source.level = {cathodicCurrenAmplitude[cycleNumber]}")
            while (elapsed_time < anodicPulseWidth[cycleNumber] + waveformParameters["interPulseInterval"]):
                elapsed_time, sourceCurrent, measureVoltage = SMU_get_measurement(instr, numDigits = 9)
                cycles.append(cycleNumber + 1)
                sources.append(sourceCurrent)
                relativeTimeIn.append(elapsed_time)
                measurements.append(measureVoltage)
            instr.write(f"smu.source.level = {anodicCurrenAmplitude[cycleNumber]}")
            while (elapsed_time < anodicPulseWidth[cycleNumber] + cathodicPulseWidth[cycleNumber] + waveformParameters["interPulseInterval"]):
                elapsed_time, sourceCurrent, measureVoltage = SMU_get_measurement(instr, numDigits = 9)
                cycles.append(cycleNumber + 1)
                sources.append(sourceCurrent)
                relativeTimeIn.append(elapsed_time)
                measurements.append(measureVoltage)
            instr.write("smu.source.level = 0")
            while (elapsed_time < anodicPulseWidth[cycleNumber] + cathodicPulseWidth[cycleNumber] + 2 * waveformParameters["interPulseInterval"]):
               elapsed_time, sourceCurrent, measureVoltage = SMU_get_measurement(instr, numDigits = 9)
               cycles.append(cycleNumber + 1)
               sources.append(sourceCurrent)
               relativeTimeIn.append(elapsed_time)
               measurements.append(measureVoltage)

    return instr

def main():
    from waveform_parameters import waveformParameters

    keithley = SMU_biphasic_current_pulse_train(waveformParameters)
    SMU_close(keithley)
    relativeTimeOut = fix_time_jumps(relativeTimeIn)
    
    # Export data into .csv file
    dataHeader = 'Time,Current,Voltage,Cycle Number'
    dataOut = column_stack((relativeTimeOut, sources, measurements, cycles))
    title = 'STTR1008_4mA'
    SMU_export_data(dataOut, title, dataHeader)

    # Plot current and voltage vs time
    SMU_yyplot(relativeTimeOut, measurements, sources, title, "Time (seconds)", "Measured Voltage (V)", "Current Output (A)")
    
if __name__ == '__main__':
    main()