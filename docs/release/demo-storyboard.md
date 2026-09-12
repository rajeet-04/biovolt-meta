# Demo storyboard

| Segment | Duration | One question answered | Proof shown |
| --- | ---: | --- | --- |
| Problem and system | 30 s | What is BioVolt measuring and controlling? | Device/evidence/access state. |
| Electrical outcome | 40 s | What is the BPV output now or in the selected history? | Voltage, current, power, units, freshness. |
| Optical/scientific context | 30 s | Is OD680/biomass/CO2 eligible? | Calibration provenance or explicit `Unavailable`. |
| Experiment/control | 80 s | How is the run bounded safely? | Mode, command ID, ACK/rejection, applied state, local firmware safety. |
| Results | 60 s | Is the Passive/Adaptive comparison eligible? | Matched duration, coverage, gain or reason code. |
| Trace/export | 30 s | Can the headline be independently checked? | Experiment ID, evidence class, calibration revision, CSV export. |
| Offline resilience | 30 s | Does the local system survive upstream loss? | Local UI stays available; tunnel failure is isolated. |

Total target: 4:00, leaving a one-minute recovery margin. Every screen answers
one primary question. Technical depth is revealed only when it supports the
current claim; warnings and provenance remain visible.
