#pragma once

#include <cstdint>

struct SafetyLimits {
  uint8_t pwmMin{0};
  uint8_t pwmMax{255};
  uint32_t mixerMaxRuntimeMs{10000};
  uint32_t mixerCooldownMs{60000};

  SafetyLimits() = default;
  SafetyLimits(uint8_t minPwm, uint8_t maxPwm, uint32_t maxRuntimeMs, uint32_t cooldownMs)
      : pwmMin(minPwm), pwmMax(maxPwm), mixerMaxRuntimeMs(maxRuntimeMs), mixerCooldownMs(cooldownMs) {}
};

class SafetyPolicy {
 public:
  explicit SafetyPolicy(SafetyLimits limits) : limits_(limits) {}

  void setLimits(SafetyLimits limits) { limits_ = limits; }
  uint8_t clampPwm(int requested) const;
  bool canStartMixer(uint64_t nowMs) const;
  void noteMixerStarted(uint64_t nowMs);
  bool mixerMustStop(uint64_t nowMs) const;
  void noteMixerStopped(uint64_t nowMs);

 private:
  SafetyLimits limits_;
  uint64_t mixerStartedMs_{0};
  uint64_t mixerStoppedMs_{0};
  bool mixerRunning_{false};
  bool hasStopped_{false};
};
