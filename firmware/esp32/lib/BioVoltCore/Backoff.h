#pragma once

#include <cstdint>

inline uint32_t reconnectDelayMs(uint32_t attempt) {
  // ponytail: cap exponential backoff before shifting to avoid overflow.
  const uint32_t cappedAttempt = attempt > 4 ? 4 : attempt;
  uint32_t base = 1000u << cappedAttempt;
  return base > 10000u ? 10000u : base;
}
