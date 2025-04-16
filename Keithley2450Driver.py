#!/usr/bin/env python3

from os import chdir, mkdir, path
from time import strftime

import matplotlib.pyplot as plt
from numpy import array, savetxt
from pyvisa import ResourceManager, errors

from experimental_configs import DATA_PATH

elapsed_time = []
sources = []
measurements = []


def smu_config(source_mode, measure_mode, source_level, limit_value):
    """smu_config initializes the Keithley 2450 Source Meter.
    The Keithley 2450 is opened as a visa resource and reset.

    source_mode  -> the mode of the source output (e.g DC_CURRENT or DC_VOLTAGE)

    measure_mode -> the mode of the measured signal (e.g DC_VOLTAGE or DC_CURRENT)

    source_level -> the amplitude of the source output (if sourcing current, this value
    must be in the range [-1.05, 1.05] A. If sourcing voltage, this value must be
    in the range [-210 and 210] V.

    limit_value  -> aka. the compliance. This value prevents the instrument from
    sourcing a voltage or current over a set value to prevent damage to the device
    under test. e.g if you are sourcing 1 mA current to an electrode with a an impedance
    of 10 kOhm, the lowest allowable voltage limit is 1 mA * 10 kOhm = 10V. Setting a
    limit lower than 10V limits the source.
    """
    # Initialize the resource manager and open Keithley 2450 SourceMeter
    # This smu is listed as a resource with the alias Keithley2450_CWRU
    rm = ResourceManager()
    listed_resources = rm.list_resources()

    try:
        instr = rm.open_resource("Keithley2450_CWRU")
    except errors.VisaIOError:
        instrument_resource_string = listed_resources[0]
        instr = rm.open_resource(instrument_resource_string)

    instr.read_termination = instr.write_termination = "\n"

    print(f'Instrument ID: {instr.query("*IDN?")}')
    # Reset instrument
    instr.write("reset()")
    instr.write("defbuffer1.clear()")
    instr.timeout = 5000

    # Measure Settings
    instr.write(f"smu.measure.func = smu.FUNC_{measure_mode}")
    instr.write("smu.measure.autorange = smu.ON")
    instr.write("smu.measure.sense = smu.SENSE_4WIRE")
    instr.write("smu.measure.terminals = smu.TERMINALS_FRONT")
    # Turn on the source readback function to record
    # the actual source value being outputted
    instr.write("smu.source.readback = smu.ON")

    # Source Settings
    instr.write(f"smu.source.func = smu.FUNC_{source_mode}")
    instr.write("smu.source.offmode = smu.OFFMODE_HIGHZ")
    instr.write(f"smu.source.level = {source_level}")
    if source_mode == "DC_CURRENT":
        instr.write(f"smu.source.vlimit.level = {limit_value}")
    else:
        instr.write(f"smu.source.ilimit.level = {limit_value}")

    ## Reset timer
    instr.write("timer.cleartime()")

    return instr


def smu_get_measurement(instr, num_digits=9):
    """smu_get_measurement reads the following data from the Keithley 2450's default
    reading buffer, defbuffer1:
    - the time of each measurement (float)
    - the source value (float)
    - the measurement value (float)
    The default number of digits (9) can be adjusted if more/less precision is needed.
    """

    instr.write("smu.measure.read(defbuffer1)")
    measurement = instr.query("print(defbuffer1.readings[defbuffer1.n])")
    source = instr.query("print(defbuffer1.sourcevalues[defbuffer1.n])")
    elapsed_time = instr.query("print(timer.gettime())")

    return (round(float(x), num_digits) for x in (elapsed_time, source, measurement))


def svmi_cycle(instr, source_level, limit_value, delay_time, num_digits: int):
    # Start Charging
    instr.write(f"smu.source.level = {source_level}")
    instr.write("smu.source.output = smu.ON")
    # Measure the current when the electrode is first charged
    initial_time, initial_source, initial_measurement = smu_get_measurement(
        instr, num_digits
    )

    print(initial_time, initial_source, initial_measurement)
    elapsed_time.append(initial_time)
    sources.append(initial_source)
    measurements.append(initial_measurement)

    # keep taking readings until the measured value is smaller than your compliance (limit value)
    while True:
        new_time, new_source, new_measurement = smu_get_measurement(instr, num_digits)
        print(new_time, new_source, new_measurement)
        elapsed_time.append(new_time)
        sources.append(new_source)
        measurements.append(new_measurement)
        if measurements[-1] >= limit_value:
            break
        instr.write(f"delay({delay_time})")


def smu_export_data(dataOut, fileName, dataHeader, formatString="%f"):
    """Export data in .csv file format"""

    dataRepositoryPath = DATA_PATH
    chdir(dataRepositoryPath)
    dataSessionPath = strftime("%Y-%m-%d")
    try:
        mkdir(dataSessionPath)
        chdir(dataSessionPath)
    except FileExistsError:
        chdir(dataSessionPath)

    # Automatically find the next available trial number
    trial_number = 1
    while True:
        dataOutFileName = f"{fileName}_trial{trial_number}.csv"
        if not path.exists(dataOutFileName):
            break
        trial_number += 1

    with open(dataOutFileName, "w") as fp:
        fp.writelines(dataHeader + "\n")
        savetxt(fp, dataOut, delimiter=",", fmt=formatString)

    return dataOutFileName


def smu_xyplot(xPoints, yPoints, xLabel="", yLabel="", figureTitle=""):
    fig, ax1 = plt.subplots()
    fig.suptitle(figureTitle, fontsize=12)
    ax1.grid()
    color = "tab:red"
    ax1.set_xlabel(xLabel)
    ax1.set_ylabel(yLabel, color=color)
    ax1.plot(array(xPoints), array(yPoints), color=color)
    ax1.tick_params(axis="y", labelcolor=color)

    dataRepositoryPath = DATA_PATH
    chdir(dataRepositoryPath)
    dataSessionPath = strftime("%Y-%m-%d")
    try:
        mkdir(dataSessionPath)
        chdir(dataSessionPath)
    except FileExistsError:
        chdir(dataSessionPath)

    # Automatically find the next available trial number
    trial_number = 1
    while True:
        figure_file_name = f"{figureTitle}_trial{trial_number}.png"
        if not path.exists(figure_file_name):
            break
        trial_number += 1

    plt.savefig(figure_file_name)
    plt.show()

    return figure_file_name


def smu_yyplot(
    xPoints, y1Points, y2Points, figureTitle, xLabel="", y1Label="", y2Label=""
):
    """smu_yyplot uses  matplotlib.pyplot to plot two dependent variables (e.g current and voltage)
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

    col = "#0072BD"
    ax1.set_xlabel(xLabel)
    ax1.set_ylabel(y1Label, color=col, weight="bold")
    ax1.plot(array(xPoints), array(y1Points), color=col)
    ax1.tick_params(axis="y", labelcolor=col)
    ax1.ticklabel_format(axis="y", style="plain")
    ax2 = ax1.twinx()  # instantiate a second Axes that shares the same x-axis

    col = "#D95319"
    ax2.set_ylabel(y2Label, color=col, weight="bold")
    ax2.plot(array(xPoints), array(y2Points), color=col)
    ax2.tick_params(axis="y", labelcolor=col)
    ax2.ticklabel_format(axis="y", style="scientific", scilimits=(-3, 3))

    dataRepositoryPath = DATA_PATH
    chdir(dataRepositoryPath)
    dataSessionPath = strftime("%Y-%m-%d")
    try:
        mkdir(dataSessionPath)
        chdir(dataSessionPath)
    except FileExistsError:
        chdir(dataSessionPath)
    # Automatically find the next available trial number
    trial_number = 1
    while True:
        figure_file_name = f"{figureTitle}_trial{trial_number}.png"
        if not path.exists(figure_file_name):
            break
        trial_number += 1

    plt.savefig(figure_file_name)
    plt.show()


def fix_time_jumps(timeIn):
    time_jumps = []
    for i in range(1, len(timeIn) - 1):
        if timeIn[i] - timeIn[i - 1] < 0:  # time jump occurred if dt is negative
            time_jumps.append(timeIn[i - 1])

    cumulative_time_jumps = [0]
    for i in range(len(time_jumps)):
        cumulative_time_jumps.append(sum(time_jumps[: i + 1]))

    j = 0
    timeOut = [timeIn[0]]
    for i in range(1, len(timeIn)):
        if timeIn[i] - timeIn[i - 1] < 0:
            j += 1

        timeOut.append(timeIn[i] + cumulative_time_jumps[j])

    return timeOut


def smu_close(instr):
    """Turn off the output, clear the buffer and close the VISA instrument"""
    instr.write("smu.source.output = smu.OFF")
    instr.write("defbuffer1.clear()")
    instr.close()
