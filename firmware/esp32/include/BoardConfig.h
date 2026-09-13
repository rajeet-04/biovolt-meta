#pragma once

namespace BoardConfig {
constexpr int kI2cSda = 21;
constexpr int kI2cScl = 22;
constexpr int kDs18b20Pin = 19;
constexpr int kProbeLed680Pin = 25;
constexpr int kGrowLedPwmPin = 26;
constexpr int kMixerPin = 27;
constexpr uint8_t kAds1115Address = 0x48;
constexpr uint8_t kBh1750Address = 0x23;
constexpr uint8_t kBpvChannel = 0;
constexpr uint8_t kOpticalChannel = 1;
}
