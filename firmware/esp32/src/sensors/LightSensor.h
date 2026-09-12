#pragma once

#include <BH1750.h>

#include "SensorTypes.h"

class LightSensor {
 public:
  bool begin();
  SensorValue<float> readLux();

 private:
  BH1750 sensor_;
  bool healthy_{false};
};
