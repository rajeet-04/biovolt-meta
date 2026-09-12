#include "SafetyPolicy.h"

uint8_t SafetyPolicy::clampPwm(int requested) const {
  if (requested <= limits_.pwmMin) return limits_.pwmMin;
  if (requested >= limits_.pwmMax) return limits_.pwmMax;
  return static_cast<uint8_t>(requested);
}

bool SafetyPolicy::canStartMixer(uint64_t nowMs) const {
  return !mixerRunning_ && (!hasStopped_ || nowMs - mixerStoppedMs_ >= limits_.mixerCooldownMs);
}

void SafetyPolicy::noteMixerStarted(uint64_t nowMs) {
  mixerStartedMs_ = nowMs;
  mixerRunning_ = true;
}

bool SafetyPolicy::mixerMustStop(uint64_t nowMs) const {
  return mixerRunning_ && nowMs - mixerStartedMs_ >= limits_.mixerMaxRuntimeMs;
}

void SafetyPolicy::noteMixerStopped(uint64_t nowMs) {
  mixerRunning_ = false;
  mixerStoppedMs_ = nowMs;
  hasStopped_ = true;
}
