# BioVolt sensor-fault drill

With electrically safe disconnects, test DS18B20, BH1750, ADS1115/BPV, and the
BPW34 optical path. The failed field must become `null`/`Unavailable`, health
must be false, unrelated acquisition must continue, and no routine fault may
reboot the ESP32. Optical faults must also remove OD680, biomass, and CO2
eligibility until valid calibration and readings return.
