#pragma once

#include "Ads1115Sampler.h"

struct OpticalSample {
  AnalogSample receiver;
  bool ledEnabledAtSample{false};
};

class OpticalProbe {
 public:
  explicit OpticalProbe(Ads1115Sampler& adc);
  void begin();
  OpticalSample sample();

 private:
  Ads1115Sampler& adc_;
};
