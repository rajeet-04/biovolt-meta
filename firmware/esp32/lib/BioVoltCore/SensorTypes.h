#pragma once

#include <cstdint>

template <typename T>
struct SensorValue {
  T value{};
  bool valid{false};
};

struct SensorSnapshot {
  SensorValue<float> bpvVoltageMv;
  SensorValue<int16_t> bpvAdcRaw;
  SensorValue<float> bpw34VoltageMv;
  SensorValue<int16_t> bpw34Raw;
  bool led680EnabledAtSample{false};
  SensorValue<float> temperatureC;
  SensorValue<float> lux;
};
