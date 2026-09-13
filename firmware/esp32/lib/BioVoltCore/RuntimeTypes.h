#pragma once

#include <cstdint>

#include "SensorTypes.h"

struct ActuatorState {
  uint8_t growLedPwm{0};
  bool mixerOn{false};
};

enum class ControlMode { Monitor, Passive, Adaptive, Manual };

struct ControlState {
  ControlMode mode{ControlMode::Monitor};
  int8_t optimizerDirection{0};
};

struct RuntimeSnapshot {
  SensorFrame sensors;
  ActuatorState actuators;
  ControlState control;
  uint64_t sampledAtMs{0};
};
