#pragma once

#include <cstddef>

#include "TelemetryModel.h"

class TelemetrySerializer {
 public:
  static constexpr size_t kJsonCapacity = 1536;

  bool serialize(const TelemetryEnvelope& envelope, char* output, size_t outputSize,
                 size_t& written) const;
};

