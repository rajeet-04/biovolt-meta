#pragma once

#include <cstdint>
#include <string>

#include "RuntimeTypes.h"

enum class AckStatus { Accepted, Applied, Rejected, Failed };

struct DeviceAck {
  std::string commandId;
  std::string deviceId;
  AckStatus status{AckStatus::Failed};
  uint64_t uptimeMs{0};
  std::string reasonCode;
  std::string message;
  ActuatorState appliedState;
  ControlMode appliedMode{ControlMode::Monitor};
  bool includeAppliedState{false};
};
