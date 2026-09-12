#pragma once

#include <Adafruit_ADS1X15.h>

#include "SensorTypes.h"

class Ads1115Sampler {
 public:
  bool begin();
  bool healthy() const;
  AnalogSample readBpv();
  AnalogSample readOptical();

 private:
  AnalogSample readChannel(uint8_t channel);

  Adafruit_ADS1115 ads_;
  bool healthy_{false};
};
