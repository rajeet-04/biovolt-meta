#pragma once

#include <cstdint>

class GrowLightDriver {
 public:
  void begin();
  void write(uint8_t pwm);
  uint8_t appliedPwm() const;

 private:
  uint8_t appliedPwm_{0};
  bool started_{false};
};
