#pragma once

#include <cstdint>
#include <string>

struct RuntimeConfig {
  std::string wifiSsid;
  std::string wifiPassword;
  std::string backendHost;
  uint16_t backendPort{8000};
  std::string backendPath{"/ws/device"};
  std::string deviceId;
  std::string cellId;
  std::string deviceToken;
  uint8_t ledPwmMin{0};
  uint8_t ledPwmMax{255};
  uint16_t mixerMaxRuntimeS{10};
  uint16_t mixerCooldownS{60};
};
