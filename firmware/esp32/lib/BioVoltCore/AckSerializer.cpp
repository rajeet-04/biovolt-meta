#include "AckSerializer.h"

#include <ArduinoJson.h>

namespace {
const char* statusName(AckStatus status) {
  switch (status) {
    case AckStatus::Accepted: return "accepted";
    case AckStatus::Applied: return "applied";
    case AckStatus::Rejected: return "rejected";
    case AckStatus::Failed: return "failed";
  }
  return "failed";
}

const char* modeName(ControlMode mode) {
  switch (mode) {
    case ControlMode::Monitor: return "monitor";
    case ControlMode::Passive: return "passive";
    case ControlMode::Adaptive: return "adaptive";
    case ControlMode::Manual: return "manual";
  }
  return "monitor";
}
}  // namespace

bool AckSerializer::serialize(const DeviceAck& ack, char* output, size_t capacity,
                              size_t& written) const {
  if (!output || capacity == 0 || ack.commandId.empty() || ack.deviceId.empty()) return false;
  StaticJsonDocument<AckSerializer::kJsonCapacity> document;
  document["schema_version"] = "device-ack.v1";
  document["command_id"] = ack.commandId;
  document["device_id"] = ack.deviceId;
  document["status"] = statusName(ack.status);
  document["uptime_ms"] = ack.uptimeMs;
  document["reason_code"] = ack.reasonCode.empty() ? nullptr : ack.reasonCode.c_str();
  document["message"] = ack.message.empty() ? nullptr : ack.message.c_str();
  if (!ack.includeAppliedState) {
    document["applied_state"] = nullptr;
  } else {
    JsonObject state = document["applied_state"].to<JsonObject>();
    state["mode"] = modeName(ack.appliedMode);
    state["grow_led_pwm"] = ack.appliedState.growLedPwm;
    state["mixer_on"] = ack.appliedState.mixerOn;
  }
  written = serializeJson(document, output, capacity);
  return written > 0 && written < capacity;
}
