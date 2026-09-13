#include "SerialProvisioner.h"

#include <cstdlib>

#include "ConfigValidation.h"

namespace {
bool parseUnsigned(const String& value, unsigned long maximum, unsigned long* parsed) {
  if (value.isEmpty()) return false;
  char* end = nullptr;
  const unsigned long number = strtoul(value.c_str(), &end, 10);
  if (*end != '\0' || number > maximum) return false;
  *parsed = number;
  return true;
}

bool sameConfig(const RuntimeConfig& left, const RuntimeConfig& right) {
  return left.wifiSsid == right.wifiSsid && left.wifiPassword == right.wifiPassword &&
         left.backendHost == right.backendHost && left.backendPort == right.backendPort &&
         left.backendPath == right.backendPath && left.deviceId == right.deviceId &&
         left.cellId == right.cellId && left.deviceToken == right.deviceToken &&
         left.ledPwmMin == right.ledPwmMin && left.ledPwmMax == right.ledPwmMax &&
         left.mixerMaxRuntimeS == right.mixerMaxRuntimeS &&
         left.mixerCooldownS == right.mixerCooldownS;
}
}  // namespace

void SerialProvisioner::begin(const RuntimeConfig& activeConfig, ConfigStore& store) {
  activeConfig_ = activeConfig;
  draftConfig_ = activeConfig;
  store_ = &store;
  Serial.println("Serial provisioning ready; config changes require reboot");
}

void SerialProvisioner::poll() {
  while (Serial.available()) {
    const char character = static_cast<char>(Serial.read());
    if (character == '\r') continue;
    if (character == '\n') {
      handleLine(input_);
      input_ = "";
    } else if (input_.length() >= kMaxLineLength) {
      input_ = "";
      Serial.println("error: command exceeds 256 bytes");
    } else {
      input_ += character;
    }
  }
}

void SerialProvisioner::handleLine(const String& line) {
  const String command = line;
  if (command == "config show") return showDraft();
  if (command == "config discard") {
    draftConfig_ = activeConfig_;
    Serial.println("draft discarded");
    return;
  }
  if (command == "config reset") {
    if (store_) store_->clear();
    Serial.println("stored configuration reset; reboot required to apply");
    return;
  }
  if (command == "config save") {
    const auto validation = validateRuntimeConfig(draftConfig_);
    if (!validation.valid) {
      Serial.print("error: ");
      Serial.println(validation.message);
      return;
    }
    if (!store_ || !store_->save(draftConfig_)) {
      Serial.println("error: configuration was not saved");
      return;
    }
    Serial.println("saved; reboot required to apply");
    return;
  }
  if (command == "status") return showStatus();
  if (command == "reboot") {
    Serial.println("rebooting");
    delay(50);
    return ESP.restart();
  }

  const String prefix = "config set ";
  if (!command.startsWith(prefix)) {
    Serial.println("error: unknown command");
    return;
  }
  const String argument = command.substring(prefix.length());
  const int separator = argument.indexOf(' ');
  if (separator <= 0 || separator == argument.length() - 1) {
    Serial.println("error: config set requires a field and value");
    return;
  }
  if (setValue(argument.substring(0, separator), argument.substring(separator + 1))) {
    Serial.println("draft updated; save and reboot to apply");
  }
}

bool SerialProvisioner::setValue(const String& field, const String& value) {
  if (field == "ssid") draftConfig_.wifiSsid = value.c_str();
  else if (field == "wifi_password") draftConfig_.wifiPassword = value.c_str();
  else if (field == "backend_host") draftConfig_.backendHost = value.c_str();
  else if (field == "device_id") draftConfig_.deviceId = value.c_str();
  else if (field == "cell_id") draftConfig_.cellId = value.c_str();
  else if (field == "token") draftConfig_.deviceToken = value.c_str();
  else {
    unsigned long number = 0;
    const unsigned long maximum = field == "backend_port" ? 65535 :
                                  field == "pwm_min" || field == "pwm_max" ? 255 : 65535;
    if (!parseUnsigned(value, maximum, &number)) {
      Serial.println("error: invalid numeric value");
      return false;
    }
    if (field == "backend_port") draftConfig_.backendPort = number;
    else if (field == "pwm_min") draftConfig_.ledPwmMin = number;
    else if (field == "pwm_max") draftConfig_.ledPwmMax = number;
    else if (field == "mixer_max_runtime_s") draftConfig_.mixerMaxRuntimeS = number;
    else if (field == "mixer_cooldown_s") draftConfig_.mixerCooldownS = number;
    else {
      Serial.println("error: unknown configuration field");
      return false;
    }
  }
  return true;
}

void SerialProvisioner::showDraft() const {
  Serial.print("ssid="); Serial.println(draftConfig_.wifiSsid.c_str());
  Serial.println("wifi_password=<configured>");
  Serial.print("backend_host="); Serial.println(draftConfig_.backendHost.c_str());
  Serial.print("backend_port="); Serial.println(draftConfig_.backendPort);
  Serial.print("device_id="); Serial.println(draftConfig_.deviceId.c_str());
  Serial.print("cell_id="); Serial.println(draftConfig_.cellId.c_str());
  Serial.println("token=<configured>");
  Serial.print("pwm_min="); Serial.println(draftConfig_.ledPwmMin);
  Serial.print("pwm_max="); Serial.println(draftConfig_.ledPwmMax);
  Serial.print("mixer_max_runtime_s="); Serial.println(draftConfig_.mixerMaxRuntimeS);
  Serial.print("mixer_cooldown_s="); Serial.println(draftConfig_.mixerCooldownS);
}

void SerialProvisioner::showStatus() const {
  Serial.print("uptime_ms="); Serial.println(millis());
  Serial.print("free_heap_bytes="); Serial.println(ESP.getFreeHeap());
  Serial.print("device_id="); Serial.println(activeConfig_.deviceId.c_str());
  Serial.print("cell_id="); Serial.println(activeConfig_.cellId.c_str());
  Serial.print("backend_host="); Serial.println(activeConfig_.backendHost.c_str());
  Serial.print("backend_port="); Serial.println(activeConfig_.backendPort);
  Serial.print("config_pending="); Serial.println(isPending() ? "true" : "false");
}

bool SerialProvisioner::isPending() const {
  return !sameConfig(activeConfig_, draftConfig_);
}
