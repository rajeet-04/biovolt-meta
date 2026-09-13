#include "TemperatureSensor.h"

#include <cmath>

#include "BoardConfig.h"

TemperatureSensor::TemperatureSensor() : oneWire_(BoardConfig::kDs18b20Pin), sensors_(&oneWire_) {}

bool TemperatureSensor::begin() {
  sensors_.begin();
  sensors_.setResolution(10);
  sensors_.setWaitForConversion(false);
  conversionWaitMs_ = DallasTemperature::millisToWaitForConversion(10);
  started_ = sensors_.getDeviceCount() > 0;
  return started_;
}

void TemperatureSensor::poll(uint64_t nowMs) {
  if (!started_) return;
  if (converting_) {
    if (nowMs - conversionStartedMs_ < conversionWaitMs_) return;
    const float value = sensors_.getTempCByIndex(0);
    latest_.valid = value != DEVICE_DISCONNECTED_C && std::isfinite(value) && value >= -55.0F && value <= 125.0F;
    latest_.value = latest_.valid ? value : 0.0F;
    converting_ = false;
    return;
  }
  sensors_.requestTemperatures();
  conversionStartedMs_ = nowMs;
  converting_ = true;
}

SensorValue<float> TemperatureSensor::latest() const { return latest_; }
