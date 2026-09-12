# ESP32 Wiring and Pre-Power Checks

| ESP32 connection | Destination |
| --- | --- |
| GPIO 21 | I2C SDA: ADS1115 SDA and BH1750 SDA |
| GPIO 22 | I2C SCL: ADS1115 SCL and BH1750 SCL |
| GPIO 19 | DS18B20 data, with pull-up |
| GPIO 25 | 680 nm probe LED driver input |
| GPIO 26 | Grow-light MOSFET/driver PWM input |
| GPIO 27 | Mixer MOSFET/relay driver input |
| ADS1115 A0 | BPV load-voltage measurement node |
| ADS1115 A1 | BPW34 optical receiver front-end output |
| ADS1115 ADDR | `0x48` |
| BH1750 ADDR | `0x23` |

I2C modules, analog front end, driver-control inputs, and the ESP32 require a
common signal ground. Power the motor and LED loads from appropriately sized,
separate rails; no load may be driven directly from an ESP32 GPIO.

Before applying load power, verify GPIO-to-driver polarity, I2C voltage
compatibility, the DS18B20 pull-up, ADS1115 gain-range limits, BPW34 analog
front-end range, and all required common grounds. Keep actuator loads
disconnected until this check passes.

