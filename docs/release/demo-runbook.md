# BioVolt offline demo runbook

Target: the core judged sequence completes in five minutes with upstream
internet disabled. The operator chooses the highest available evidence level
at the start and says it aloud: `LIVE_WET_HARDWARE`, `MEASURED_HISTORY`, or
`SYNTHETIC_DEMO`. Never upgrade the evidence class during the presentation.

| Time | Operator action | Visible checkpoint | Evidence source |
| --- | --- | --- | --- |
| 0:00–0:30 | Open the local HTTPS URL in a fresh browser and point to the status banner. | BioVolt identity, live/stale/offline state, access mode, and evidence class are visible. | Local production build; hardware or history required for measured claim. |
| 0:30–1:10 | Open Overview and select the connected device/source. | BPV voltage, current, and power show units; no unavailable value is shown as zero. | Live wet hardware or measured telemetry history. |
| 1:10–1:40 | Open Live Data and explain the OD680 path only if dark/blank references and calibration are valid. | Optical/biomass/CO2 values show provenance or `Unavailable` with a reason. | Physical reference/calibration or explicitly demonstrative history. |
| 1:40–2:20 | Open the recorded experiment and show its state, mode, cell, and pinned calibration. | State transitions and evidence provenance are visible; no pending command is called applied. | Completed measured experiment, or synthetic demo with its label. |
| 2:20–3:00 | If a device is connected, demonstrate the safe control boundary and explain local P&O ownership. | Command ID, ACK/rejection, actual applied state, and safety mode are visible. | Live hardware only for an actuator claim; otherwise explain from recorded history. |
| 3:00–4:00 | Open Results for the matched Passive/Adaptive comparison. | Duration, coverage, eligibility/reason codes, negative gain, and calibration provenance agree with the API. | Measured paired experiments only for a performance claim. |
| 4:00–4:30 | Open the CSV export and point to experiment ID/evidence/calibration fields. | The headline can be traced to raw/exported evidence. | Local export. |
| 4:30–5:00 | Disconnect upstream internet or show the already-disabled state; refresh the local PWA. | Local operation remains available; only optional public tunnel status changes. | Local stack; no hardware claim is added. |

Do not open every navigation item, call P&O machine learning, imply a gain
before Results eligibility, or hide stale, simulation, read-only, or safety
banners. If a step cannot meet its checkpoint, use the documented fallback
ladder and state the reason before continuing.
