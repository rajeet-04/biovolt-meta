#pragma once

#include <cstdint>

#include "ControlBaseline.h"
#include "RuntimeTypes.h"
#include "SafetyPolicy.h"

#include "GrowLightDriver.h"
#include "MixerDriver.h"

class ActuatorController {
 public:
  ActuatorController(GrowLightDriver& growLight, MixerDriver& mixer, SafetyPolicy& safety);
  void begin();
  ActuatorState apply(const ActuatorRequest& request, uint64_t nowMs);
  ActuatorState enforceTimeouts(uint64_t nowMs);
  ActuatorState state() const;

 private:
  GrowLightDriver& growLight_;
  MixerDriver& mixer_;
  SafetyPolicy& safety_;
  ActuatorState state_;
};
