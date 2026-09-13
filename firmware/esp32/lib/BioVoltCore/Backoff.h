#pragma once

#include <cstdint>

inline uint32_t reconnectDelayMs(uint32_t attempt) {
  uint32_t base = 1000u << attempt;
  return base > 10000u ? 10000u : base;
}
