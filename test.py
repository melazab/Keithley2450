import pyvisa
import time

numDigits = 5


rm = pyvisa.ResourceManager()
keithley =  rm.open_resource("Keithley2450_CWRU")

keithley.write("reset()")
keithley.write("defbuffer1.clear()")
keithley.write("timer.cleartime()")
keithley.read_termination = '\n'
keithley.write_termination = '\n'

# Source Settings
keithley.write("smu.source.func = smu.FUNC_DC_CURRENT")
keithley.write("smu.source.level = 0.001") # 1 mA 
keithley.write("smu.source.vlimit.level = 0.5") # compliance = 0.5 V
keithley.write("smu.source.autorange = smu.ON")
keithley.write("smu.source.offmode = smu.OFFMODE_HIGHZ")
# Measure Settings
keithley.write("smu.measure.func = smu.FUNC_DC_VOLTAGE")
keithley.write("smu.measure.autorange = smu.ON")
keithley.write("smu.measure.terminals = smu.TERMINALS_FRONT")
keithley.write("smu.source.readback = smu.ON")

#change display to user screen
#keithley.write("display.changescreen(display.SCREEN_USER_SWIPE)")

# Turn on output
try:
    keithley.write("smu.source.readback = smu.ON")
    keithley.write("smu.source.output = smu.ON")
    while True:
        keithley.write("smu.measure.read(defbuffer1)")

        measurement = keithley.query("print(defbuffer1.readings[defbuffer1.n])")
        source = keithley.query("print(defbuffer1.sourcevalues[defbuffer1.n])")
        elapsed_time = keithley.query("print(timer.gettime())")

        print(elapsed_time, source, measurement)
        time.sleep(1)
except KeyboardInterrupt:
        pass

keithley.write("smu.source.output = smu.OFF")
keithley.write("defbuffer1.clear()")
keithley.close()
