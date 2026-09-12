#pragma once

#include "Ads1115Sampler.h"
#include "LightSensor.h"
#include "OpticalProbe.h"
#include "SensorTypes.h"
#include "TemperatureSensor.h"

class SensorManager {
 public:
  void begin();
  SensorFrame sample(uint64_t nowMs);

 private:
  Ads1115Sampler adc_;
  TemperatureSensor temperature_;
  LightSensor light_;
  OpticalProbe optical_{adc_};
};
