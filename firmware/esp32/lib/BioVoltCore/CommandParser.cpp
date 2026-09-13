#include "CommandParser.h"

#include <ArduinoJson.h>
#include <cctype>
#include <cstring>

namespace {
bool isUuid(const char* value) {
  if (!value || std::strlen(value) != 36) return false;
  for (size_t index = 0; index < 36; ++index) {
    if (index == 8 || index == 13 || index == 18 || index == 23) {
      if (value[index] != '-') return false;
    } else if (!((value[index] >= '0' && value[index] <= '9') ||
                 (value[index] >= 'a' && value[index] <= 'f'))) {
      return false;
    }
  }
  return true;
}

bool copyString(JsonVariantConst value, std::string& target, size_t maxLength) {
  if (!value.is<const char*>()) return false;
  const char* text = value.as<const char*>();
  if (!text || std::strlen(text) == 0 || std::strlen(text) > maxLength) return false;
  target = text;
  return true;
}

ParseCommandResult invalid(const char* reason) {
  ParseCommandResult result;
  result.reasonCode = reason;
  return result;
}

ParseCommandResult invalid(ParseCommandResult result, const char* reason) {
  result.valid = false;
  result.reasonCode = reason;
  return result;
}
}  // namespace

ParseCommandResult parseDeviceCommand(const char* payload, size_t length) {
  if (!payload || length == 0 || length > 2048) return invalid("invalid_payload");
  StaticJsonDocument<2048> document;
  if (deserializeJson(document, payload, length) != DeserializationError::Ok) {
    return invalid("invalid_payload");
  }
  JsonObjectConst root = document.as<JsonObjectConst>();
  if (root.size() != 9 || root["schema_version"] != "device-command.v1" ||
      !root.containsKey("command_id") || !root.containsKey("device_id") ||
      !root.containsKey("experiment_id") || !root["issued_at"].is<const char*>() ||
      !root["expires_at"].is<const char*>() || !root.containsKey("ttl_ms") ||
      !root.containsKey("kind") || !root.containsKey("payload")) {
    return invalid("invalid_payload");
  }

  ParseCommandResult result;
  if (!copyString(root["command_id"], result.command.commandId, 36) ||
      !isUuid(result.command.commandId.c_str())) {
    return invalid(result, "invalid_payload");
  }
  if (!copyString(root["device_id"], result.command.deviceId, 64)) {
    return invalid(result, "invalid_payload");
  }
  if (!root["experiment_id"].isNull() &&
      !copyString(root["experiment_id"], result.command.experimentId, 64)) {
    return invalid(result, "invalid_payload");
  }
  const int ttl = root["ttl_ms"] | 0;
  if (ttl < 1 || ttl > 600000) return invalid(result, "invalid_payload");
  result.command.ttlMs = static_cast<uint32_t>(ttl);

  const char* kind = root["kind"] | "";
  JsonObjectConst body = root["payload"].as<JsonObjectConst>();
  if (!body) return invalid(result, "invalid_payload");
  if (std::strcmp(kind, "set_mode") == 0) {
    if (body.size() != 1 || !body.containsKey("mode")) {
      return invalid(result, "invalid_payload");
    }
    const char* mode = body["mode"] | "";
    if (std::strcmp(mode, "monitor") == 0) result.command.requestedMode = ControlMode::Monitor;
    else if (std::strcmp(mode, "passive") == 0) result.command.requestedMode = ControlMode::Passive;
    else if (std::strcmp(mode, "manual") == 0) result.command.requestedMode = ControlMode::Manual;
    else if (std::strcmp(mode, "adaptive") == 0) result.command.requestedMode = ControlMode::Adaptive;
    else return invalid(result, "invalid_payload");
    result.command.kind = CommandKind::SetMode;
  } else if (std::strcmp(kind, "set_led_pwm") == 0) {
    if (body.size() != 1 || !body["pwm"].is<int>() || body["pwm"].as<int>() < 0 ||
        body["pwm"].as<int>() > 255) {
      return invalid(result, "invalid_payload");
    }
    result.command.requestedPwm = static_cast<uint8_t>(body["pwm"].as<int>());
    result.command.kind = CommandKind::SetLedPwm;
  } else if (std::strcmp(kind, "set_mixer") == 0) {
    if (body.size() != 1 || !body["on"].is<bool>()) {
      return invalid(result, "invalid_payload");
    }
    result.command.requestedMixerOn = body["on"].as<bool>();
    result.command.kind = CommandKind::SetMixer;
  } else if (std::strcmp(kind, "request_status") == 0) {
    if (body.size() != 0) return invalid(result, "invalid_payload");
    result.command.kind = CommandKind::RequestStatus;
  } else if (std::strcmp(kind, "safe_stop") == 0) {
    if (body.size() != 0) return invalid(result, "invalid_payload");
    result.command.kind = CommandKind::SafeStop;
  } else {
    return invalid(result, "unsupported_command");
  }
  result.valid = true;
  return result;
}
