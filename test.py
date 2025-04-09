from Keithley2450Driver import fix_time_jumps

if __name__ == "__main__":
    time1 = [ 0.1 * val for val in range(0, 10)]
    time2 = [ 0.2 * val for val in range(0, 10)]
    time3 = [ 0.3 * val for val in range(0, 10)]
    timeIn = time1 + time2 + time3
    print(len(timeIn))
    timeOut = fix_time_jumps(timeIn)
    print(len(timeOut))