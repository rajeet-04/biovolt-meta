#include <string>

#include <unity.h>

#include "ConfigValidation.h"

void setUp() {}
void tearDown() {}

RuntimeConfig validConfig() {
  RuntimeConfig config;
  config.wifiSsid = "BioVolt-Hotspot";
  config.wifiPassword = "secret";
  config.backendHost = "192.168.1.10";
  config.deviceId = "biovolt-01";
  config.cellId = "cell-a";
  config.deviceToken = "token";
  return config;
}

void test_valid_config_passes() {
  const auto result = validateRuntimeConfig(validConfig());
  TEST_ASSERT_TRUE(result.valid);
  TEST_ASSERT_NULL(result.message);
}

void test_required_network_and_identity_fields_fail_when_blank() {
  for (const char* field : {"ssid", "host", "device_id", "cell_id", "token"}) {
    auto config = validConfig();
    if (std::string(field) == "ssid") config.wifiSsid = "";
    if (std::string(field) == "host") config.backendHost = "";
    if (std::string(field) == "device_id") config.deviceId = "";
    if (std::string(field) == "cell_id") config.cellId = "";
    if (std::string(field) == "token") config.deviceToken = "";
    TEST_ASSERT_FALSE(validateRuntimeConfig(config).valid);
  }
}

void test_invalid_bounds_and_path_fail() {
  auto config = validConfig();
  config.backendPort = 0;
  TEST_ASSERT_FALSE(validateRuntimeConfig(config).valid);

  config = validConfig();
  config.backendPath = "ws/device";
  TEST_ASSERT_FALSE(validateRuntimeConfig(config).valid);

  config = validConfig();
  config.deviceId = std::string(65, 'x');
  TEST_ASSERT_FALSE(validateRuntimeConfig(config).valid);

  config = validConfig();
  config.ledPwmMin = 200;
  config.ledPwmMax = 100;
  TEST_ASSERT_FALSE(validateRuntimeConfig(config).valid);

  config = validConfig();
  config.mixerMaxRuntimeS = 0;
  TEST_ASSERT_FALSE(validateRuntimeConfig(config).valid);
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_valid_config_passes);
  RUN_TEST(test_required_network_and_identity_fields_fail_when_blank);
  RUN_TEST(test_invalid_bounds_and_path_fail);
  return UNITY_END();
}
