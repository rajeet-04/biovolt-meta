#include "Ads1115Sampler.h"

#include <Wire.h>

#include "BoardConfig.h"

bool Ads1115Sampler::begin() {
  Wire.begin(BoardConfig::kI2cSda, BoardConfig::kI2cScl);
  Wire.beginTransmission(BoardConfig::kAds1115Address);
  const bool acknowledged = Wire.endTransmission() == 0;
  if (!acknowledged || !ads_.begin(BoardConfig::kAds1115Address)) {
    healthy_ = false;
    return false;
  }
  ads_.setGain(GAIN_ONE);
  healthy_ = true;
  return true;
}

bool Ads1115Sampler::healthy() const { return healthy_; }

AnalogSample Ads1115Sampler::readBpv() {
  return readChannel(BoardConfig::kBpvChannel);
}

AnalogSample Ads1115Sampler::readOptical() {
  return readChannel(BoardConfig::kOpticalChannel);
}

AnalogSample Ads1115Sampler::readChannel(uint8_t channel) {
  if (!healthy_) return {};
  AnalogSample sample;
  sample.raw = ads_.readADC_SingleEnded(channel);
  sample.millivolts = ads_.computeVolts(sample.raw) * 1000.0F;
  sample.valid = true;
  return sample;
}
