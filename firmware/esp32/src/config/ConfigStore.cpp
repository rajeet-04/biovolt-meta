#include "ConfigStore.h"

#include <Arduino.h>
#include <ArduinoJson.h>

#include "ConfigValidation.h"

namespace {
constexpr char kNamespace[] = "biovolt";
constexpr char kConfigKey[] = "config_v1";
constexpr size_t kConfigDocumentCapacity = 1024;

void printSafeLoadReason(const char* reason) {
  Serial.print("Config fallback: ");
  Serial.println(reason);
}
}  // namespace

bool ConfigStore::begin() {
  started_ = preferences_.begin(kNamespace, false);
  if (!started_) Serial.println("Config storage unavailable");
  return started_;
}

RuntimeConfig ConfigStore::load(const RuntimeConfig& fallback) {
  if (!started_ || !preferences_.isKey(kConfigKey)) return fallback;

  const String blob = preferences_.getString(kConfigKey, "");
  StaticJsonDocument<kConfigDocumentCapacity> document;
  if (deserializeJson(document, blob)) {
    printSafeLoadReason("stored configuration is unreadable");
    return fallback;
  }
  if (document["version"] != 1) {
    printSafeLoadReason("stored configuration version is unsupported");
    return fallback;
  }

  RuntimeConfig config;
  config.wifiSsid = document["wifi_ssid"].as<const char*>() ?: "";
  config.wifiPassword = document["wifi_password"].as<const char*>() ?: "";
  config.backendHost = document["backend_host"].as<const char*>() ?: "";
  config.backendPort = document["backend_port"] | 0;
  config.backendPath = document["backend_path"].as<const char*>() ?: "";
  config.deviceId = document["device_id"].as<const char*>() ?: "";
  config.cellId = document["cell_id"].as<const char*>() ?: "";
  config.deviceToken = document["device_token"].as<const char*>() ?: "";
  config.ledPwmMin = document["led_pwm_min"] | 0;
  config.ledPwmMax = document["led_pwm_max"] | 255;
  config.mixerMaxRuntimeS = document["mixer_max_runtime_s"] | 0;
  config.mixerCooldownS = document["mixer_cooldown_s"] | 0;

  if (!validateRuntimeConfig(config).valid) {
    printSafeLoadReason("stored configuration is invalid");
    return fallback;
  }
  return config;
}

bool ConfigStore::save(const RuntimeConfig& config) {
  if (!started_ || !validateRuntimeConfig(config).valid) return false;

  StaticJsonDocument<kConfigDocumentCapacity> document;
  document["version"] = 1;
  document["wifi_ssid"] = config.wifiSsid;
  document["wifi_password"] = config.wifiPassword;
  document["backend_host"] = config.backendHost;
  document["backend_port"] = config.backendPort;
  document["backend_path"] = config.backendPath;
  document["device_id"] = config.deviceId;
  document["cell_id"] = config.cellId;
  document["device_token"] = config.deviceToken;
  document["led_pwm_min"] = config.ledPwmMin;
  document["led_pwm_max"] = config.ledPwmMax;
  document["mixer_max_runtime_s"] = config.mixerMaxRuntimeS;
  document["mixer_cooldown_s"] = config.mixerCooldownS;

  String blob;
  if (serializeJson(document, blob) == 0 || document.overflowed()) return false;
  return preferences_.putString(kConfigKey, blob) == blob.length();
}

void ConfigStore::clear() {
  if (started_) preferences_.remove(kConfigKey);
}
