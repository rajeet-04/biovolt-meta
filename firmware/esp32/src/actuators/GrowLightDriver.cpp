#include "GrowLightDriver.h"

#include <Arduino.h>

#include "BoardConfig.h"

namespace {
constexpr uint8_t kPwmChannel = 0;
constexpr uint32_t kPwmFrequencyHz = 5000;
constexpr uint8_t kPwmResolutionBits = 8;
}

void GrowLightDriver::begin() {
  ledcSetup(kPwmChannel, kPwmFrequencyHz, kPwmResolutionBits);
  ledcWrite(kPwmChannel, 0);
  ledcAttachPin(BoardConfig::kGrowLedPwmPin, kPwmChannel);
  appliedPwm_ = 0;
  started_ = true;
}

void GrowLightDriver::write(uint8_t pwm) {
  if (!started_) return;
  ledcWrite(kPwmChannel, pwm);
  appliedPwm_ = pwm;
}

uint8_t GrowLightDriver::appliedPwm() const { return appliedPwm_; }
