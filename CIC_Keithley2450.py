#!/usr/bin/env python3

## The pulseWidth parameter in smu_biphasic_current_pulse
## implies the cathodic and anodic pulses have equal duration

from pathlib import Path
from time import time

import matplotlib.pyplot as plt
from numpy import array, column_stack

from experimental_configs import ELECTRODE_ID, waveform_parameters
from Keithley2450Driver import (
    fix_time_jumps,
    smu_close,
    smu_config,
    smu_export_data,
    smu_get_measurement,
    smu_yyplot,
)

relative_time_in = []
sources = []
measurements = []
cycles = []


def smu_monophasic_current_pulse(waveform_parameters, polarity):
    """
    waveform_parameters -> Dict that contains the waveform parameters

    polarity -> String that describes whether the current is "anodic" or "cathodic"

    """
    if abs(waveform_parameters["currentAmplitude"][polarity]) > 1.05:
        print("Error: smu_monophasic_current_pulse")
        print("Current Amplitude must be in the range [-1.05, 1.05] A")
        exit

    instr = smu_config(
        "DC_CURRENT",
        "DC_VOLTAGE",
        waveform_parameters["currentAmplitude"][polarity],
        waveform_parameters["complianceVoltage"],
    )

    instr.write("smu.source.output = smu.ON")  # Turn on output
    instr.write("timer.cleartime()")  # Reset Timer
    tic = time()
    while True:
        elapsed_time, source_current, measure_voltage = smu_get_measurement(
            instr, num_digits=9
        )
        relative_time_in.append(time() - tic)
        sources.append(source_current)
        measurements.append(measure_voltage)
        cycles.append(1)

        if elapsed_time > waveform_parameters["pulseWidth"][polarity]:
            break
    return instr


def smu_biphasic_current_pulse(waveform_parameters):
    if (waveform_parameters["currentAmplitude"]["anodic"] < 0) or (
        waveform_parameters["currentAmplitude"]["anodic"] > 1.05
    ):
        print("Error: smu_asymmetric_biphasic_current_pulse")
        print("Anodic current amplitude must be in the range [0, 1.05] A")
        exit
    elif (waveform_parameters["currentAmplitude"]["cathodic"] < -1.05) or (
        waveform_parameters["currentAmplitude"]["cathodic"] > 0
    ):
        print("Error: smu_asymmetric_biphasic_current_pulse")
        print("Cathodic current amplitude must be in the range [-1.05, 0] A")
        exit

    if waveform_parameters["anodicFirst"]:
        instr = smu_config(
            "DC_CURRENT",
            "DC_VOLTAGE",
            waveform_parameters["currentAmplitude"]["anodic"],
            waveform_parameters["complianceVoltage"],
        )
    else:
        instr = smu_config(
            "DC_CURRENT",
            "DC_VOLTAGE",
            waveform_parameters["currentAmplitude"]["cathodic"],
            waveform_parameters["complianceVoltage"],
        )

    instr.write("smu.source.output = smu.ON")  # Turn on output
    instr.write("timer.cleartime()")  # Reset Timer
    tic = time()  # Time 0 of relative_time_in array
    while True:
        elapsed_time, source_current, measure_voltage = smu_get_measurement(
            instr, num_digits=9
        )
        relative_time_in.append(time() - tic)
        sources.append(source_current)
        measurements.append(measure_voltage)
        cycles.append(1)  # only 1 cycle not a train
        if elapsed_time > waveform_parameters["pulseWidth"]["anodic"]:
            break

    instr.write("timer.cleartime()")  # Reset Timer
    if waveform_parameters["anodicFirst"]:
        instr.write(
            f"smu.source.level = {waveform_parameters["currentAmplitude"]["cathodic"]}"
        )  # Switch from anodic to cathodic
    else:  # otherwise if cathodicFirst then switch from cathodic to anodic
        instr.write(
            f"smu.source.level = {waveform_parameters["currentAmplitude"]["anodic"]}"
        )
    while True:
        elapsed_time = smu_get_measurement(instr, num_digits=9)
        elapsed_time, source_current, measure_voltage = smu_get_measurement(
            instr, num_digits=9
        )
        relative_time_in.append(time() - tic)
        sources.append(source_current)
        measurements.append(measure_voltage)
        cycles.append(1)  # only 1 cycle not a train
        if elapsed_time > waveform_parameters["pulseWidth"]["cathodic"]:
            break

    instr.write("smu.source.output = smu.OFF")
    return instr


def smu_monophasic_current_pulse_train(waveform_parameters, polarity):
    """
    waveform_parameters -> Dict that contains the waveform parameters

    polarity -> String that describes whether the current is "anodic" or "cathodic"

    """
    if waveform_parameters["numPulses"] < 0:
        print("Error: smu_monophasic_current_pulse_train")
        print("Number of pulses must be non-negative")
        exit

    if abs(waveform_parameters["currentAmplitude"][polarity]) > 1.05:
        print("Error: smu_monophasic_current_pulse_train")
        print("Current Amplitude must be in the range [-1.05, 1.05] A")
        exit

    instr = smu_config(
        "DC_CURRENT",
        "DC_VOLTAGE",
        waveform_parameters["currentAmplitude"][polarity],
        waveform_parameters["complianceVoltage"],
    )
    try:
        iter(waveform_parameters["pulseWidth"][polarity])
        pulseWidth = waveform_parameters["pulseWidth"][polarity]

    except TypeError as te:
        pulseWidth = [
            waveform_parameters["pulseWidth"][polarity]
            for _ in range(0, waveform_parameters["numPulses"])
        ]

    for cycle_number in range(0, waveform_parameters["numPulses"]):
        instr.write("timer.cleartime()")  # Reset Timer
        instr.write("smu.source.output = smu.ON")  # Turn on output
        elapsed_time = 0
        while elapsed_time < pulseWidth[cycle_number]:
            elapsed_time, source_current, measure_voltage = smu_get_measurement(
                instr, num_digits=9
            )
            cycles.append(cycle_number + 1)
            sources.append(source_current)
            relative_time_in.append(elapsed_time)
            measurements.append(measure_voltage)

        # instr.write("smu.source.output = smu.OFF")
        instr.write("smu.source.level = 0")
        while (
            elapsed_time
            < pulseWidth[cycle_number] + waveform_parameters["interPulseInterval"]
        ):
            elapsed_time, source_current, measure_voltage = smu_get_measurement(
                instr, num_digits=9
            )
            cycles.append(cycle_number + 1)
            sources.append(source_current)
            relative_time_in.append(elapsed_time)
            measurements.append(measure_voltage)
        instr.write(
            f"smu.source.level = {waveform_parameters["currentAmplitude"][polarity]}"
        )
    return instr


def smu_biphasic_current_pulse_train(waveform_parameters):
    try:
        iter(waveform_parameters["pulseWidth"]["anodic"])
        anodicPulseWidth = waveform_parameters["pulseWidth"]["anodic"]
    except TypeError as te:
        anodicPulseWidth = [
            waveform_parameters["pulseWidth"]["anodic"]
            for _ in range(0, waveform_parameters["numPulses"])
        ]

    try:
        iter(waveform_parameters["pulseWidth"]["cathodic"])
        cathodicPulseWidth = waveform_parameters["pulseWidth"]["cathodic"]
    except TypeError as te:
        cathodicPulseWidth = [
            waveform_parameters["pulseWidth"]["cathodic"]
            for _ in range(0, waveform_parameters["numPulses"])
        ]

    # Handle the case where the current amplitude is not constant through out cycles
    # e.g current amplitude could be [1, 2, 4, 8] which represents a waveform whose
    # amplitude doubles every cycle.
    try:
        iter(waveform_parameters["currentAmplitude"]["anodic"])
        anodic_current_amplitude = waveform_parameters["currentAmplitude"]["anodic"]
    except TypeError as te:
        anodic_current_amplitude = [
            waveform_parameters["currentAmplitude"]["anodic"]
            for _ in range(0, waveform_parameters["numPulses"])
        ]

    try:
        iter(waveform_parameters["currentAmplitude"]["cathodic"])
        cathodic_current_amplitude = waveform_parameters["currentAmplitude"]["cathodic"]
    except TypeError as te:
        cathodic_current_amplitude = [
            waveform_parameters["currentAmplitude"]["cathodic"]
            for _ in range(0, waveform_parameters["numPulses"])
        ]

    if waveform_parameters["anodicFirst"]:
        instr = smu_config(
            "DC_CURRENT",
            "DC_VOLTAGE",
            anodic_current_amplitude[0],
            waveform_parameters["complianceVoltage"],
        )
        for cycle_number in range(0, waveform_parameters["numPulses"]):
            instr.write("timer.cleartime()")  # Reset Timer
            instr.write("smu.source.level = 0")
            instr.write("smu.source.output = smu.ON")  # Turn on output
            elapsed_time = 0
            while elapsed_time < waveform_parameters["interPulseInterval"]:
                elapsed_time, source_current, measure_voltage = smu_get_measurement(
                    instr, num_digits=9
                )
                cycles.append(cycle_number + 1)
                sources.append(source_current)
                relative_time_in.append(elapsed_time)
                measurements.append(measure_voltage)
            instr.write(f"smu.source.level = {anodic_current_amplitude[cycle_number]}")
            while (
                elapsed_time
                < anodicPulseWidth[cycle_number]
                + waveform_parameters["interPulseInterval"]
            ):
                elapsed_time, source_current, measure_voltage = smu_get_measurement(
                    instr, num_digits=9
                )
                cycles.append(cycle_number + 1)
                sources.append(source_current)
                relative_time_in.append(elapsed_time)
                measurements.append(measure_voltage)
            instr.write("smu.source.level = 0")
            while (
                elapsed_time
                < anodicPulseWidth[cycle_number]
                + waveform_parameters["interPhaseDelay"]
                + waveform_parameters["interPulseInterval"]
            ):
                elapsed_time, source_current, measure_voltage = smu_get_measurement(
                    instr, num_digits=9
                )
                cycles.append(cycle_number + 1)
                sources.append(source_current)
                relative_time_in.append(elapsed_time)
                measurements.append(measure_voltage)
            instr.write(
                f"smu.source.level = {cathodic_current_amplitude[cycle_number]}"
            )
            while (
                elapsed_time
                < anodicPulseWidth[cycle_number]
                + waveform_parameters["interPhaseDelay"]
                + cathodicPulseWidth[cycle_number]
                + waveform_parameters["interPulseInterval"]
            ):
                elapsed_time, source_current, measure_voltage = smu_get_measurement(
                    instr, num_digits=9
                )
                cycles.append(cycle_number + 1)
                sources.append(source_current)
                relative_time_in.append(elapsed_time)
                measurements.append(measure_voltage)
            instr.write("smu.source.level = 0")
            while (
                elapsed_time
                < anodicPulseWidth[cycle_number]
                + waveform_parameters["interPhaseDelay"]
                + cathodicPulseWidth[cycle_number]
                + 2 * waveform_parameters["interPulseInterval"]
            ):
                elapsed_time, source_current, measure_voltage = smu_get_measurement(
                    instr, num_digits=9
                )
                cycles.append(cycle_number + 1)
                sources.append(source_current)
                relative_time_in.append(elapsed_time)
                measurements.append(measure_voltage)
    else:  # cathodic first pulses
        instr = smu_config(
            "DC_CURRENT",
            "DC_VOLTAGE",
            cathodic_current_amplitude[0],
            waveform_parameters["complianceVoltage"],
        )
        for cycle_number in range(0, waveform_parameters["numPulses"]):
            instr.write("timer.cleartime()")  # Reset Timer
            instr.write("smu.source.level = 0")
            instr.write("smu.source.output = smu.ON")  # Turn on output
            elapsed_time = 0
            while elapsed_time < waveform_parameters["interPulseInterval"]:
                elapsed_time, source_current, measure_voltage = smu_get_measurement(
                    instr, num_digits=9
                )
                cycles.append(cycle_number + 1)
                sources.append(source_current)
                relative_time_in.append(elapsed_time)
                measurements.append(measure_voltage)
            # Cathodic phase
            instr.write(
                f"smu.source.level = {cathodic_current_amplitude[cycle_number]}"
            )
            while (
                elapsed_time
                < cathodicPulseWidth[cycle_number]
                + waveform_parameters["interPulseInterval"]
            ):
                elapsed_time, source_current, measure_voltage = smu_get_measurement(
                    instr, num_digits=9
                )
                cycles.append(cycle_number + 1)
                sources.append(source_current)
                relative_time_in.append(elapsed_time)
                measurements.append(measure_voltage)
            # Interphase delay (if non-zero)
            instr.write("smu.source.level = 0")
            while (
                elapsed_time
                < waveform_parameters["interPhaseDelay"]
                + cathodicPulseWidth[cycle_number]
                + waveform_parameters["interPulseInterval"]
            ):
                elapsed_time, source_current, measure_voltage = smu_get_measurement(
                    instr, num_digits=9
                )
                cycles.append(cycle_number + 1)
                sources.append(source_current)
                relative_time_in.append(elapsed_time)
                measurements.append(measure_voltage)

            # Anodic phase
            instr.write(f"smu.source.level = {anodic_current_amplitude[cycle_number]}")
            while (
                elapsed_time
                < cathodicPulseWidth[cycle_number]
                + anodicPulseWidth[cycle_number]
                + waveform_parameters["interPulseInterval"]
                + waveform_parameters["interPhaseDelay"]
            ):
                elapsed_time, source_current, measure_voltage = smu_get_measurement(
                    instr, num_digits=9
                )
                cycles.append(cycle_number + 1)
                sources.append(source_current)
                relative_time_in.append(elapsed_time)
                measurements.append(measure_voltage)
            instr.write("smu.source.level = 0")
            while (
                elapsed_time
                < anodicPulseWidth[cycle_number]
                + waveform_parameters["interPhaseDelay"]
                + cathodicPulseWidth[cycle_number]
                + 2 * waveform_parameters["interPulseInterval"]
            ):
                elapsed_time, source_current, measure_voltage = smu_get_measurement(
                    instr, num_digits=9
                )
                cycles.append(cycle_number + 1)
                sources.append(source_current)
                relative_time_in.append(elapsed_time)
                measurements.append(measure_voltage)

    return instr


def main():

    keithley = smu_biphasic_current_pulse_train(waveform_parameters)
    smu_close(keithley)
    relative_time_out = fix_time_jumps(relative_time_in)

    # Export data into .csv file
    data_header = "Time,Current,Voltage,Cycle Number"
    data_out = column_stack((relative_time_out, sources, measurements, cycles))
    title = ELECTRODE_ID
    smu_export_data(data_out, title, data_header)

    # Plot current and voltage vs time
    smu_yyplot(
        relative_time_out,
        measurements,
        sources,
        title,
        "Time (seconds)",
        "Measured Voltage (V)",
        "Current Output (A)",
    )


if __name__ == "__main__":
    main()
