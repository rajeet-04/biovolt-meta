#pragma once

#include <cstdint>

struct ActuatorState {
  uint8_t growLedPwm{0};
  bool mixerOn{false};
};

enum class ControlMode { Monitor, Passive, Adaptive, Manual };

struct ControlState {
  ControlMode mode{ControlMode::Monitor};
  int8_t optimizerDirection{0};
};
