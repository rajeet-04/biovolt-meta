# Judge access state matrix

| State | Required public copy | Allowed actions |
| --- | --- | --- |
| Live measured | Read-only judge view; measured evidence | Results, safe export |
| Live simulator | Read-only judge view; Synthetic demo data | Results, safe export |
| Stale/offline | Telemetry stale or backend disconnected | Read cached/read-only views |
| Tunnel down | Local operator remains healthy | None publicly; local operation continues |
| No completed run | No completed experiment yet | Browse setup/status only |
| Ineligible comparison | Unavailable with visible quality/provenance reason | Inspect data and export |
