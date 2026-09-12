#include "ActuatorController.h"

ActuatorController::ActuatorController(GrowLightDriver& growLight, MixerDriver& mixer,
                                       SafetyPolicy& safety)
    : growLight_(growLight), mixer_(mixer), safety_(safety) {}

void ActuatorController::begin() {
  growLight_.begin();
  mixer_.begin();
  state_ = {};
}

ActuatorState ActuatorController::apply(const ActuatorRequest& request, uint64_t nowMs) {
  enforceTimeouts(nowMs);
  state_.growLedPwm = safety_.clampPwm(request.growLedPwm);
  growLight_.write(state_.growLedPwm);

  if (request.mixerOn && !state_.mixerOn && safety_.canStartMixer(nowMs)) {
    mixer_.write(true);
    safety_.noteMixerStarted(nowMs);
    state_.mixerOn = true;
  } else if (!request.mixerOn && state_.mixerOn) {
    mixer_.write(false);
    safety_.noteMixerStopped(nowMs);
    state_.mixerOn = false;
  }
  return state_;
}

ActuatorState ActuatorController::enforceTimeouts(uint64_t nowMs) {
  if (state_.mixerOn && safety_.mixerMustStop(nowMs)) {
    mixer_.write(false);
    safety_.noteMixerStopped(nowMs);
    state_.mixerOn = false;
  }
  return state_;
}

ActuatorState ActuatorController::state() const { return state_; }
