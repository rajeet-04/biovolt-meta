# Phase 3 Firmware Bench Checklist

Build and upload only after the wiring pre-power checks pass:

```bash
cd firmware/esp32
pio run -e esp32dev -t upload
pio device monitor -b 115200
```

Provision through serial without recording credentials in logs:

```text
config set ssid <laptop-hotspot-ssid>
config set wifi_password <password>
config set backend_host <laptop-hotspot-ip>
config set backend_port 8000
config set device_id biovolt-01
config set cell_id cell-a
config set token <shared-token>
config save
reboot
```

For simulated acceptance, retain `BIOVOLT_SIMULATED_SENSORS` and confirm
changing, healthy raw values. For real hardware, remove that build flag and
check ADS1115 A0 against a known reference, verify the optical pulse changes
BPW34 A1, confirm DS18B20 updates without stalling telemetry, and cover the
BH1750 to lower lux. Disconnect each sensor individually: its field must
become `null` with a false health flag and the ESP32 must not reboot.

