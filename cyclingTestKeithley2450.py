#!/usr/bin/env python

## To-do: Display real-time measurements on SMU

import pyvisa
import numpy as np
import time
import matplotlib.pyplot as plt
from scipy import integrate
from pathlib import Path
import os

measurements = []


def SMU_config(sourceMode, measureMode, sourceLevel, limitValue):
    # Initialize the resource manager and open Keithley 2450 SourceMeter
    # This SMU is listed as a resource with the alias Keithley2450_CWRU
    rm = pyvisa.ResourceManager()
    listedResources = rm.list_resources()
    try:
        instr = rm.open_resource("Keithley2450_CWRU")
    except:
        instrumentResourceString = listedResources[0]
        instr = rm.open_resource(instrumentResourceString)

    instr.read_termination = instr.write_termination = '\n'
    instr.write("*IDN?")
    instrInfo = instr.read()
    print(f"Instrument ID: {instrInfo}")
    # Reset instrument
    instr.write("reset()")
    instr.write("defbuffer1.clear()")
    instr.timeout = 10000
    
    # General Settings
    instr.write("display.changescreen(display.SCREEN_USER_SWIPE)")
    # Measure Settings
    instr.write(f"smu.measure.func = smu.FUNC_{measureMode}")
    instr.write("smu.measure.autorange = smu.ON")
    instr.write("smu.measure.sense = smu.SENSE_2WIRE") #Change to 4WIRE if needed
    instr.write("smu.measure.terminals = smu.TERMINALS_FRONT")
    # Turn on the voltage source readback function to measure the
    # electrode voltage as it is charging or discharging.
    instr.write("smu.source.readback = smu.ON")

    # Source Settings
    instr.write(f"smu.source.func = smu.FUNC_{sourceMode}")
    instr.write("smu.source.offmode = smu.OFFMODE_HIGHZ")
    instr.write(f"smu.source.level = {sourceLevel}")
    if (sourceMode == "DC_CURRENT"):
        instr.write(f"smu.source.vlimit.level = {limitValue}")
    else:
        instr.write(f"smu.source.ilimit.level = {limitValue}")

    return instr

def SMU_get_measurement(instr, numDigits: int) -> float:
    instr.write("smu.measure.read()")
    measurementStr = instr.query("print(defbuffer1.readings[defbuffer1.endindex])")
    measurementFloat = round(float(measurementStr), numDigits)
    return measurementFloat

def SVMI_cycle(instr,sourceLevel, dI, delayTimeBetweenSamples, numDigits:int):
    # Start Charging
    instr.write(f"smu.source.level = {sourceLevel}")
    instr.write("smu.source.output = smu.ON")
    # Measure the current when the electrode is first charged
    initialMeasurement = SMU_get_measurement(instr, numDigits)
    print(initialMeasurement)
    measurements.append(initialMeasurement)
       
    # keep taking readings until the change in current is smaller than dI
    while True:
        newMeasurement = SMU_get_measurement(instr,numDigits)
        print(newMeasurement)
        measurements.append(newMeasurement)
        if (abs(measurements[-1] - measurements[-2]) < dI):
            break
        instr.write(f"delay({delayTimeBetweenSamples})")


def SMU_close(instr):
    instr.write("smu.source.output = smu.OFF")
    instr.write("defbuffer1.clear()")
    instr.close()

def main():
    SOURCE_LEVEL = 0.5
    LIMIT_VALUE = 0.02

    MEASURE_PERIOD = 0.5 # seconds between consecutive measurement samples
    NUM_DIGITS = 9 #round measurements to NUM_DIGITS
    NUM_CYCLES = 5
    FIG_TITLE = "Cycle testing on STTR tripolar electrode"
    SOURCE_MODE = "DC_VOLTAGE"
    SOURCE_UNIT = "VOLT" if SOURCE_MODE == "DC_VOLTAGE" else "AMP"
    MEASURE_MODE = "DC_CURRENT"
    MEASURE_UNIT = "AMP"

    timeStr = time.strftime("%H_%M_%S")
    # timestamp will be appended to the exported filename
    keithley = SMU_config(SOURCE_MODE,MEASURE_MODE,SOURCE_LEVEL,LIMIT_VALUE)
    deltaMeasure = 1e-6 #  
    for cycleNumber in range(1,NUM_CYCLES + 1):
        print(f"Start cycle {cycleNumber}")
         # Start charge
        print(f" Charging the electrode to {SOURCE_LEVEL} {SOURCE_UNIT}S...\n")
        SVMI_cycle(keithley, sourceLevel = SOURCE_LEVEL,  dI = deltaMeasure, delayTimeBetweenSamples = MEASURE_PERIOD, numDigits= NUM_DIGITS)
        
        # Start discharge
        print(f"Discharging the electrode to -{SOURCE_LEVEL} {SOURCE_UNIT}S...\n")
        SVMI_cycle(keithley,sourceLevel = -SOURCE_LEVEL , dI = deltaMeasure, delayTimeBetweenSamples = MEASURE_PERIOD, numDigits= NUM_DIGITS)
    
    # clean up
    SMU_close(keithley)

    # export results to .csv file
    measurementsOut = np.asarray(measurements)
    sourcesOut  = SOURCE_LEVEL* np.sign(measurementsOut)
    
    dataRepositoryPath = Path.home()/"Box/Electrical Nerve Block Institute/Data/\
ElectrodeTesting/STTR/Cycle testing/"
    os.chdir(dataRepositoryPath)
    dataSessionPath = time.strftime("%Y-%m-%d")
    try:
        os.mkdir(dataSessionPath)
        os.chdir(dataSessionPath)
    except FileExistsError:
        os.chdir(dataSessionPath)
    dataOutFileName = FIG_TITLE
    np.savetxt(timeStr + FIG_TITLE +".csv", np.column_stack((sourcesOut, measurementsOut)), delimiter=",")

    # Calculate energy stored in Watt-hours for each cycle
    
    # Plot current and voltage vs time
    
    fig, ax1 = plt.subplots()
    fig.suptitle(FIG_TITLE, fontsize=12)
    ax1.grid()

    color = 'tab:red'
    ax1.set_xlabel('time (s)')
    ax1.set_ylabel(f"{MEASURE_MODE} ({MEASURE_UNIT})", color=color)
    ax1.plot(measurementsOut, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second Axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel(f"{SOURCE_MODE} ({SOURCE_UNIT})", color=color)  # we already handled the x-label with ax1
    ax2.plot(sourcesOut, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.savefig(FIG_TITLE + timeStr + ".png")
    plt.show()
    


    
if __name__ == "__main__":
    main()
    