#!/usr/bin/env python3

from Keithley2450Driver import SMU_config, SMU_close, SMU_get_measurement

def ohmmeter(sourceMode, sourceLevel = 10, limitValue =  is_4wire = False):
    instr = SMU_config(sourceMode = "DC_CURRENT", measureMode = "RESISTANCE", sourceLevel, limitValue)
    if is_4wire:
        instr.write("smu.measure.sense = smu.SENSE_4WIRE")
    
    SMU_get_measurement(instr, numDigits = 9)
def main():
    

if __name__ == '__main__':
    main()