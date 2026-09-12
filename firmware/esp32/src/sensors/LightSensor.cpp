#include "LightSensor.h"

#include <cmath>
#include <Wire.h>

#include "BoardConfig.h"

bool LightSensor::begin() {
  Wire.begin(BoardConfig::kI2cSda, BoardConfig::kI2cScl);
  healthy_ = sensor_.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, BoardConfig::kBh1750Address, &Wire);
  return healthy_;
}

SensorValue<float> LightSensor::readLux() {
  if (!healthy_ || !sensor_.measurementReady(false)) return {};
  const float value = sensor_.readLightLevel();
  if (!std::isfinite(value) || value < 0.0F) return {};
  SensorValue<float> result;
  result.value = value;
  result.valid = true;
  return result;
}
