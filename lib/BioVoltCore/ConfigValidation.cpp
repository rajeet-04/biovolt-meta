#include "ConfigValidation.h"
#include <string>

ConfigValidationResult validateRuntimeConfig(const RuntimeConfig& config) {
    if (config.wifiSsid.empty()) {
        return {false, "ssid required"};
    }
    if (config.wifiPassword.empty()) {
        return {false, "wifi_password required"};
    }
    if (config.backendHost.empty()) {
        return {false, "backend_host required"};
    }
    if (config.backendPort == 0) {
        return {false, "backend_port must be > 0"};
    }
    if (config.backendPath.empty() || config.backendPath[0] != '/') {
        return {false, "backend_path must start with /"};
    }
    if (config.deviceId.empty()) {
        return {false, "device_id required"};
    }
    if (config.deviceId.length() > 64) {
        return {false, "device_id too long"};
    }
    if (config.cellId.empty()) {
        return {false, "cell_id required"};
    }
    if (config.cellId.length() > 64) {
        return {false, "cell_id too long"};
    }
    if (config.deviceToken.empty()) {
        return {false, "device_token required"};
    }
    if (config.ledPwmMin > config.ledPwmMax) {
        return {false, "led_pwm_min > led_pwm_max"};
    }
    if (config.mixerMaxRuntimeS == 0) {
        return {false, "mixer_max_runtime_s must be > 0"};
    }
    if (config.mixerCooldownS < 0) {
        return {false, "mixer_cooldown_s must be >= 0"};
    }
    if (config.ledPwmMin > 255 || config.ledPwmMax > 255) {
        return {false, "led_pwm must be in range 0..255"};
    }

    return {true, nullptr};
}
