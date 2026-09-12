#pragma once

#include "RuntimeTypes.h"

struct ActuatorRequest {
  int growLedPwm{0};
  bool mixerOn{false};
};

inline ControlState phase3ControlState() { return {}; }
inline ActuatorRequest phase3DefaultActuatorRequest() { return {}; }
