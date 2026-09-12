#pragma once

#include <cstddef>

#include "AckModel.h"

class AckSerializer {
 public:
  static constexpr size_t kJsonCapacity = 768;
  bool serialize(const DeviceAck& ack, char* output, size_t capacity, size_t& written) const;
};
