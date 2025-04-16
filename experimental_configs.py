"""Experimental configurations for a CIC biphasic current pulse train"""

from pathlib import Path

DATA_PATH = Path.home() / "Documents/STTR_DATA"  # Add your own data path
ELECTRODE_ID = "STTR_H4mm_ID13P86mm"
NUM_PULSES = 2
INTER_PULSE_INTERVAL = 2
INTER_PHASE_DELAY = 10
ANODIC_PULSE_WIDTH = 0.1 * 60  # pulse width in minutes
CATHODIC_PULSE_WIDTH = 0.2 * 60  # pulse width in minutes

ANODIC_CURRENT_AMPLITUDE = 1e-3
CATHODIC_CURRENT_AMPLITUDE = -0.5e-3
COMPLIANCE_VOLTAGE = 210
waveform_parameters = {
    "numPulses": NUM_PULSES,
    "interPulseInterval": INTER_PULSE_INTERVAL,
    "interPhaseDelay": INTER_PHASE_DELAY,
    "pulseWidth": {"anodic": ANODIC_PULSE_WIDTH, "cathodic": CATHODIC_PULSE_WIDTH},
    "currentAmplitude": {
        "anodic": ANODIC_CURRENT_AMPLITUDE,
        "cathodic": CATHODIC_CURRENT_AMPLITUDE,
    },
    "anodicFirst": False,
    "complianceVoltage": COMPLIANCE_VOLTAGE,
}
