#include "ConfigValidation.h"

ConfigValidationResult validateRuntimeConfig(const RuntimeConfig& config) {
  if (config.wifiSsid.empty()) return {false, "ssid required"};
  if (config.wifiPassword.empty()) return {false, "wifi password required"};
  if (config.backendHost.empty()) return {false, "backend host required"};
  if (config.backendPort == 0) return {false, "backend port required"};
  if (config.backendPath.empty() || config.backendPath.front() != '/') return {false, "backend path invalid"};
  if (config.deviceId.empty() || config.deviceId.size() > 64) return {false, "device id invalid"};
  if (config.cellId.empty() || config.cellId.size() > 64) return {false, "cell id invalid"};
  if (config.deviceToken.empty()) return {false, "device token required"};
  if (config.ledPwmMin > config.ledPwmMax) return {false, "pwm range invalid"};
  if (config.mixerMaxRuntimeS == 0) return {false, "mixer runtime required"};
  return {true, nullptr};
}
