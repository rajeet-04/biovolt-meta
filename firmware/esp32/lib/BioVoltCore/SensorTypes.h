#pragma once

#include <cstdint>

template <typename T>
struct SensorValue {
  T value{};
  bool valid{false};
};

struct AnalogSample {
  int16_t raw{0};
  float millivolts{0.0F};
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

struct SensorHealth {
  bool ads1115Ok{false};
  bool bpw34Ok{false};
  bool temperatureOk{false};
  bool lightSensorOk{false};
};

struct SensorFrame {
  SensorSnapshot snapshot;
  SensorHealth health;
};
