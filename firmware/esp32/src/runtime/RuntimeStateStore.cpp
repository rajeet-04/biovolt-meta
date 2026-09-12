#include "RuntimeStateStore.h"

bool RuntimeStateStore::begin() {
  mutex_ = xSemaphoreCreateMutex();
  return mutex_ != nullptr;
}

void RuntimeStateStore::updateSensors(const SensorFrame& frame, uint64_t sampledAtMs) {
  if (!mutex_ || xSemaphoreTake(mutex_, portMAX_DELAY) != pdTRUE) return;
  snapshot_.sensors = frame;
  snapshot_.sampledAtMs = sampledAtMs;
  xSemaphoreGive(mutex_);
}

void RuntimeStateStore::updateActuators(const ActuatorState& state) {
  if (!mutex_ || xSemaphoreTake(mutex_, portMAX_DELAY) != pdTRUE) return;
  snapshot_.actuators = state;
  xSemaphoreGive(mutex_);
}

void RuntimeStateStore::updateControl(const ControlState& state) {
  if (!mutex_ || xSemaphoreTake(mutex_, portMAX_DELAY) != pdTRUE) return;
  snapshot_.control = state;
  xSemaphoreGive(mutex_);
}

RuntimeSnapshot RuntimeStateStore::snapshot() {
  if (!mutex_ || xSemaphoreTake(mutex_, portMAX_DELAY) != pdTRUE) return {};
  const RuntimeSnapshot result = snapshot_;
  xSemaphoreGive(mutex_);
  return result;
}
