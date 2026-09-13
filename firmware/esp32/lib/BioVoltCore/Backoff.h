#pragma once

#include <cstdint>

inline uint32_t reconnectDelayMs(uint32_t attempt) {
  // ponytail: 1000u << attempt overflows past attempt=22 (uint32 wrap) and is
  // UB at shift >= 32. Cap attempt at the call site when wired into the Wi-Fi
  // reconnect loop in Phase 3.6.
  uint32_t base = 1000u << attempt;
  return base > 10000u ? 10000u : base;
}
