#pragma once

#include <DallasTemperature.h>

#include "SensorTypes.h"

class TemperatureSensor {
 public:
  TemperatureSensor();
  bool begin();
  void poll(uint64_t nowMs);
  SensorValue<float> latest() const;

 private:
  OneWire oneWire_;
  DallasTemperature sensors_;
  SensorValue<float> latest_;
  uint64_t conversionStartedMs_{0};
  uint16_t conversionWaitMs_{0};
  bool converting_{false};
  bool started_{false};
};
