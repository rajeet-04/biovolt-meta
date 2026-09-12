#pragma once

#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>

#include "RuntimeTypes.h"

class RuntimeStateStore {
 public:
  bool begin();
  void updateSensors(const SensorFrame& frame, uint64_t sampledAtMs);
  void updateActuators(const ActuatorState& state);
  void updateControl(const ControlState& state);
  RuntimeSnapshot snapshot();

 private:
  RuntimeSnapshot snapshot_;
  SemaphoreHandle_t mutex_{nullptr};
};
