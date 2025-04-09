NUM_PULSES = 2
INTER_PULSE_INTERVAL = 2
INTER_PHASE_DELAY = 0 # NOT IMPLEMENTED YET
ANODIC_PULSE_WIDTH = CATHODIC_PULSE_WIDTH = 180
CATHODIC_CURRENT_AMPLITUDE = -4e-3
ANODIC_CURRENT_AMPLITUDE = 4e-3
COMPLIANCE_VOLTAGE = 5
waveformParameters = {
    "numPulses": NUM_PULSES,
    "interPulseInterval": INTER_PULSE_INTERVAL,
    "interPhaseDelay": INTER_PHASE_DELAY,
    "pulseWidth": {
        "anodic": ANODIC_PULSE_WIDTH,
        "cathodic": CATHODIC_PULSE_WIDTH
    },
    "currentAmplitude": {
        "anodic":ANODIC_CURRENT_AMPLITUDE,
        "cathodic": CATHODIC_CURRENT_AMPLITUDE
    },
    "anodicFirst": True,
    "complianceVoltage": COMPLIANCE_VOLTAGE
}