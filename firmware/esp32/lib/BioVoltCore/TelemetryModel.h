#pragma once

#include <cstddef>
#include <cstdint>

#include "RuntimeTypes.h"

struct TelemetryEnvelope {
  const char* deviceId{nullptr};
  const char* cellId{nullptr};
  uint32_t sequence{0};
  uint64_t uptimeMs{0};
  RuntimeSnapshot runtime;
};

