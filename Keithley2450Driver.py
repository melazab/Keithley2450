#!/usr/bin/env python3

from os import chdir, mkdir
from time import strftime, time

import matplotlib.pyplot as plt
from numpy import array, savetxt
from pyvisa import ResourceManager

from waveform_parameters import EXPORT_DATA_PATH

elapsed_time = []
sources = []
measurements = []


def SMU_config(sourceMode, measureMode, sourceLevel, limitValue):
    """SMU_config initializes the Keithley 2450 Source Meter.
    The Keithley 2450 is opened as a visa resource and reset.

    sourceMode  -> the mode of the source output (e.g DC_CURRENT or DC_VOLTAGE)

    measureMode -> the mode of the measured signal (e.g DC_VOLTAGE or DC_CURRENT)

    sourceLevel -> the amplitude of the source output (if sourcing current, this value
    must be in the range [-1.05, 1.05] A. If sourcing voltage, this value must be
    in the range [-210 and 210] V.

    limitValue  -> aka. the compliance. This value prevents the instrument from
    sourcing a voltage or current over a set value to prevent damage to the device
    under test. e.g if you are sourcing 1 mA current to an electrode with a an impedance
    of 10 kOhm, the lowest allowable voltage limit is 1 mA * 10 kOhm = 10V. Setting a
    limit lower than 10V limits the source.
    """
    # Initialize the resource manager and open Keithley 2450 SourceMeter
    # This SMU is listed as a resource with the alias Keithley2450_CWRU
    rm = ResourceManager()
    listedResources = rm.list_resources()
    try:
        instr = rm.open_resource("Keithley2450_CWRU")
    except:
        instrumentResourceString = listedResources[0]
        instr = rm.open_resource(instrumentResourceString)

    instr.read_termination = instr.write_termination = "\n"

    print(f'Instrument ID: {instr.query("*IDN?")}')
    # Reset instrument
    instr.write("reset()")
    instr.write("defbuffer1.clear()")
    instr.timeout = 5000

    # Measure Settings
    instr.write(f"smu.measure.func = smu.FUNC_{measureMode}")
    instr.write("smu.measure.autorange = smu.ON")
    instr.write("smu.measure.sense = smu.SENSE_4WIRE")  # Change to 2WIRE if needed
    instr.write("smu.measure.terminals = smu.TERMINALS_FRONT")
    # Turn on the source readback function to record
    # the actual source value being outputted
    instr.write("smu.source.readback = smu.ON")

    # Source Settings
    instr.write(f"smu.source.func = smu.FUNC_{sourceMode}")
    instr.write("smu.source.offmode = smu.OFFMODE_HIGHZ")
    instr.write(f"smu.source.level = {sourceLevel}")
    if sourceMode == "DC_CURRENT":
        instr.write(f"smu.source.vlimit.level = {limitValue}")
    else:
        instr.write(f"smu.source.ilimit.level = {limitValue}")

    ## Reset timer
    instr.write("timer.cleartime()")

    return instr


def SMU_get_measurement(instr, numDigits=9):
    """SMU_get_measurement reads the following data from the Keithley 2450's default
    reading buffer, defbuffer1: the time of each measurement, the source value and
    the measurement value that are returned as floats. The default number of digits (9)
    can be adjusted if more/less precision is needed."""

    instr.write("smu.measure.read(defbuffer1)")
    measurement = instr.query("print(defbuffer1.readings[defbuffer1.n])")
    source = instr.query("print(defbuffer1.sourcevalues[defbuffer1.n])")
    elapsed_time = instr.query("print(timer.gettime())")

    return (round(float(x), numDigits) for x in (elapsed_time, source, measurement))


def SVMI_cycle(instr, sourceLevel, limitValue, delayTimeBetweenSamples, numDigits: int):
    # Start Charging
    instr.write(f"smu.source.level = {sourceLevel}")
    instr.write("smu.source.output = smu.ON")
    # Measure the current when the electrode is first charged
    initialTime, initialSource, initialMeasurement = SMU_get_measurement(
        instr, numDigits
    )

    print(initialTime, initialSource, initialMeasurement)
    elapsed_time.append(initialTime)
    sources.append(initialSource)
    measurements.append(initialMeasurement)

    # keep taking readings until the measured value is smaller than your compliance (limit value)
    while True:
        newTime, newSource, newMeasurement = SMU_get_measurement(instr, numDigits)
        print(newTime, newSource, newMeasurement)
        elapsed_time.append(newTime)
        sources.append(newSource)
        measurements.append(newMeasurement)
        if measurements[-1] >= limitValue:
            break
        instr.write(f"delay({delayTimeBetweenSamples})")


def SMU_export_data(dataOut, fileName, dataHeader, formatString="%f"):
    """Export data in .csv file format and save on Box Drive in STTR folder"""
    dataRepositoryPath = EXPORT_DATA_PATH
    chdir(dataRepositoryPath)
    dataSessionPath = strftime("%Y-%m-%d")
    try:
        mkdir(dataSessionPath)
        chdir(dataSessionPath)
    except FileExistsError:
        chdir(dataSessionPath)

    dataOutFileName = fileName + strftime("_%H_%M_%S") + ".csv"
    with open(dataOutFileName, "w") as fp:
        fp.writelines(dataHeader + "\n")
        savetxt(fp, dataOut, delimiter=",", fmt=formatString)


def SMU_xyplot(xPoints, yPoints, xLabel="", yLabel="", figureTitle=""):
    fig, ax1 = plt.subplots()
    fig.suptitle(figureTitle, fontsize=12)
    ax1.grid()

    color = "tab:red"
    ax1.set_xlabel(xLabel)
    ax1.set_ylabel(yLabel, color=color)
    ax1.plot(array(xPoints), array(yPoints), color=color)
    ax1.tick_params(axis="y", labelcolor=color)

    dataRepositoryPath = EXPORT_DATA_PATH
    chdir(dataRepositoryPath)
    dataSessionPath = strftime("%Y-%m-%d")
    try:
        mkdir(dataSessionPath)
        chdir(dataSessionPath)
    except FileExistsError:
        chdir(dataSessionPath)
    plt.savefig(figureTitle + strftime("_%H_%M_%S") + ".png")
    plt.show()


def SMU_yyplot(
    xPoints, y1Points, y2Points, figureTitle, xLabel="", y1Label="", y2Label=""
):
    """SMU_yyplot uses  matplotlib.pyplot to plot two dependent variables (e.g current and voltage)
    versus an independent variable (e.g time). All variables are converted to numpy arrays. The
    relative_time = relative_time
    figure is saved on Box in /Date/ElectrodeTesting/STTR/YYYY_MM_DD with the file name exported as
    figureTitle_HH_MM_SS.png

    xPoints, y1Points and y2Points  --> each is a 1-D array of numbers
    figureTitle  --> string containing the figure title. The exported figure has a file name
                     with this string
    xLabel, y1Label and y2Label (optional) -> strings containing the axes labels
    """
    fig, ax1 = plt.subplots()
    fig.suptitle(figureTitle, fontsize=12)
    ax1.grid()

    COLOR = "#0072BD"
    ax1.set_xlabel(xLabel)
    ax1.set_ylabel(y1Label, color=COLOR, weight="bold")
    ax1.plot(array(xPoints), array(y1Points), color=COLOR)
    ax1.tick_params(axis="y", labelcolor=COLOR)
    ax1.ticklabel_format(axis="y", style="plain")
    ax2 = ax1.twinx()  # instantiate a second Axes that shares the same x-axis

    COLOR = "#D95319"
    ax2.set_ylabel(y2Label, color=COLOR, weight="bold")
    ax2.plot(array(xPoints), array(y2Points), color=COLOR)
    ax2.tick_params(axis="y", labelcolor=COLOR)
    ax2.ticklabel_format(axis="y", style="scientific", scilimits=(-3, 3))

    dataRepositoryPath = EXPORT_DATA_PATH
    chdir(dataRepositoryPath)
    dataSessionPath = strftime("%Y-%m-%d")
    try:
        mkdir(dataSessionPath)
        chdir(dataSessionPath)
    except FileExistsError:
        chdir(dataSessionPath)

    plt.savefig(figureTitle + strftime("_%H_%M_%S") + ".png")
    plt.show()


def fix_time_jumps(timeIn):
    timeJumps = []
    for i in range(1, len(timeIn) - 1):
        if timeIn[i] - timeIn[i - 1] < 0:  # time jump occurred if dt is negative
            timeJumps.append(timeIn[i - 1])

    cumulativeTimeJumps = [0]
    for i in range(len(timeJumps)):
        cumulativeTimeJumps.append(sum(timeJumps[: i + 1]))

    j = 0
    timeOut = [timeIn[0]]
    for i in range(1, len(timeIn)):
        if timeIn[i] - timeIn[i - 1] < 0:
            j += 1

        timeOut.append(timeIn[i] + cumulativeTimeJumps[j])

    return timeOut


def SMU_close(instr):
    instr.write("smu.source.output = smu.OFF")
    instr.write("defbuffer1.clear()")
    instr.close()

