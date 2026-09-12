#pragma once

#include <cstdint>
#include <cstring>
#include <string>

#include "RuntimeTypes.h"

enum class CommandKind { SetMode, SetLedPwm, SetMixer, RequestStatus, SafeStop };

struct DeviceCommand {
  std::string commandId;
  std::string deviceId;
  std::string experimentId;
  uint32_t ttlMs{0};
  uint64_t receivedAtMs{0};
  CommandKind kind{CommandKind::RequestStatus};
  ControlMode requestedMode{ControlMode::Monitor};
  uint8_t requestedPwm{0};
  bool requestedMixerOn{false};
};

struct ParseCommandResult {
  bool valid{false};
  DeviceCommand command;
  std::string reasonCode;
};

struct CommandQueueItem {
  char commandId[40]{};
  char deviceId[65]{};
  char experimentId[65]{};
  uint32_t ttlMs{0};
  uint64_t receivedAtMs{0};
  CommandKind kind{CommandKind::RequestStatus};
  ControlMode requestedMode{ControlMode::Monitor};
  uint8_t requestedPwm{0};
  bool requestedMixerOn{false};
};

inline DeviceCommand commandFromQueueItem(const CommandQueueItem& item) {
  DeviceCommand command;
  command.commandId = item.commandId;
  command.deviceId = item.deviceId;
  command.experimentId = item.experimentId;
  command.ttlMs = item.ttlMs;
  command.receivedAtMs = item.receivedAtMs;
  command.kind = item.kind;
  command.requestedMode = item.requestedMode;
  command.requestedPwm = item.requestedPwm;
  command.requestedMixerOn = item.requestedMixerOn;
  return command;
}

inline bool commandToQueueItem(const DeviceCommand& command, CommandQueueItem& item) {
  if (command.commandId.size() >= sizeof(item.commandId) ||
      command.deviceId.size() >= sizeof(item.deviceId) ||
      command.experimentId.size() >= sizeof(item.experimentId)) {
    return false;
  }
  std::strncpy(item.commandId, command.commandId.c_str(), sizeof(item.commandId) - 1);
  std::strncpy(item.deviceId, command.deviceId.c_str(), sizeof(item.deviceId) - 1);
  std::strncpy(item.experimentId, command.experimentId.c_str(), sizeof(item.experimentId) - 1);
  item.ttlMs = command.ttlMs;
  item.receivedAtMs = command.receivedAtMs;
  item.kind = command.kind;
  item.requestedMode = command.requestedMode;
  item.requestedPwm = command.requestedPwm;
  item.requestedMixerOn = command.requestedMixerOn;
  return true;
}
