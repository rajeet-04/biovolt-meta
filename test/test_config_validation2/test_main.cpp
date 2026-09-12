#include <unity.h>
#include "ConfigValidation.h"
#include "RuntimeConfig.h"

void setUp() {}
void tearDown() {}

void test_valid_config_passes() {
    RuntimeConfig cfg;
    cfg.wifiSsid = "test-ssid";
    cfg.wifiPassword = "test-password";
    cfg.backendHost = "192.168.1.100";
    cfg.backendPort = 8000;
    cfg.backendPath = "/ws/device";
    cfg.deviceId = "biovolt-01";
    cfg.cellId = "cell-a";
    cfg.deviceToken = "valid-token-123";
    cfg.ledPwmMin = 0;
    cfg.ledPwmMax = 255;
    cfg.mixerMaxRuntimeS = 10;
    cfg.mixerCooldownS = 60;

    auto result = validateRuntimeConfig(cfg);
    TEST_ASSERT_TRUE(result.valid);
    TEST_ASSERT_NULL(result.message);
}

void test_blank_ssid_fails() {
    RuntimeConfig cfg;
    cfg.wifiSsid = "";
    cfg.wifiPassword = "pw";
    cfg.backendHost = "host";
    cfg.backendPort = 8000;
    cfg.backendPath = "/ws/device";
    cfg.deviceId = "id";
    cfg.cellId = "cell";
    cfg.deviceToken = "token";

    auto result = validateRuntimeConfig(cfg);
    TEST_ASSERT_FALSE(result.valid);
    TEST_ASSERT_NOT_NULL(result.message);
    TEST_ASSERT_EQUAL_STRING("ssid required", result.message);
}

void test_blank_wifi_password_fails() {
    RuntimeConfig cfg;
    cfg.wifiSsid = "ssid";
    cfg.wifiPassword = "";
    cfg.backendHost = "host";
    cfg.backendPort = 8000;
    cfg.backendPath = "/ws/device";
    cfg.deviceId = "id";
    cfg.cellId = "cell";
    cfg.deviceToken = "token";

    auto result = validateRuntimeConfig(cfg);
    TEST_ASSERT_FALSE(result.valid);
    TEST_ASSERT_EQUAL_STRING("wifi_password required", result.message);
}

void test_blank_backend_host_fails() {
    RuntimeConfig cfg;
    cfg.wifiSsid = "ssid";
    cfg.wifiPassword = "pw";
    cfg.backendHost = "";
    cfg.backendPort = 8000;
    cfg.backendPath = "/ws/device";
    cfg.deviceId = "id";
    cfg.cellId = "cell";
    cfg.deviceToken = "token";

    auto result = validateRuntimeConfig(cfg);
    TEST_ASSERT_FALSE(result.valid);
    TEST_ASSERT_EQUAL_STRING("backend_host required", result.message);
}

void test_blank_device_id_fails() {
    RuntimeConfig cfg;
    cfg.wifiSsid = "ssid";
    cfg.wifiPassword = "pw";
    cfg.backendHost = "host";
    cfg.backendPort = 8000;
    cfg.backendPath = "/ws/device";
    cfg.deviceId = "";
    cfg.cellId = "cell";
    cfg.deviceToken = "token";

    auto result = validateRuntimeConfig(cfg);
    TEST_ASSERT_FALSE(result.valid);
    TEST_ASSERT_EQUAL_STRING("device_id required", result.message);
}

void test_blank_cell_id_fails() {
    RuntimeConfig cfg;
    cfg.wifiSsid = "ssid";
    cfg.wifiPassword = "pw";
    cfg.backendHost = "host";
    cfg.backendPort = 8000;
    cfg.backendPath = "/ws/device";
    cfg.deviceId = "id";
    cfg.cellId = "";
    cfg.deviceToken = "token";

    auto result = validateRuntimeConfig(cfg);
    TEST_ASSERT_FALSE(result.valid);
    TEST_ASSERT_EQUAL_STRING("cell_id required", result.message);
}

void test_blank_device_token_fails() {
    RuntimeConfig cfg;
    cfg.wifiSsid = "ssid";
    cfg.wifiPassword = "pw";
    cfg.backendHost = "host";
    cfg.backendPort = 8000;
    cfg.backendPath = "/ws/device";
    cfg.deviceId = "id";
    cfg.cellId = "cell";
    cfg.deviceToken = "";

    auto result = validateRuntimeConfig(cfg);
    TEST_ASSERT_FALSE(result.valid);
    TEST_ASSERT_EQUAL_STRING("device_token required", result.message);
}

void test_zero_backend_port_fails() {
    RuntimeConfig cfg;
    cfg.wifiSsid = "ssid";
    cfg.wifiPassword = "pw";
    cfg.backendHost = "host";
    cfg.backendPort = 0;
    cfg.backendPath = "/ws/device";
    cfg.deviceId = "id";
    cfg.cellId = "cell";
    cfg.deviceToken = "token";

    auto result = validateRuntimeConfig(cfg);
    TEST_ASSERT_FALSE(result.valid);
    TEST_ASSERT_EQUAL_STRING("backend_port must be > 0", result.message);
}

void test_backend_path_not_starting_with_slash_fails() {
    RuntimeConfig cfg;
    cfg.wifiSsid = "ssid";
    cfg.wifiPassword = "pw";
    cfg.backendHost = "host";
    cfg.backendPort = 8000;
    cfg.backendPath = "ws/device";
    cfg.deviceId = "id";
    cfg.cellId = "cell";
    cfg.deviceToken = "token";

    auto result = validateRuntimeConfig(cfg);
    TEST_ASSERT_FALSE(result.valid);
    TEST_ASSERT_EQUAL_STRING("backend_path must start with /", result.message);
}

void test_device_id_too_long_fails() {
    RuntimeConfig cfg;
    cfg.wifiSsid = "ssid";
    cfg.wifiPassword = "pw";
    cfg.backendHost = "host";
    cfg.backendPort = 8000;
    cfg.backendPath = "/ws/device";
    cfg.deviceId = std::string(65, 'a');
    cfg.cellId = "cell";
    cfg.deviceToken = "token";

    auto result = validateRuntimeConfig(cfg);
    TEST_ASSERT_FALSE(result.valid);
    TEST_ASSERT_EQUAL_STRING("device_id too long", result.message);
}

void test_cell_id_too_long_fails() {
    RuntimeConfig cfg;
    cfg.wifiSsid = "ssid";
    cfg.wifiPassword = "pw";
    cfg.backendHost = "host";
    cfg.backendPort = 8000;
    cfg.backendPath = "/ws/device";
    cfg.deviceId = "id";
    cfg.cellId = std::string(65, 'b');
    cfg.deviceToken = "token";

    auto result = validateRuntimeConfig(cfg);
    TEST_ASSERT_FALSE(result.valid);
    TEST_ASSERT_EQUAL_STRING("cell_id too long", result.message);
}

void test_led_pwm_min_greater_than_max_fails() {
    RuntimeConfig cfg;
    cfg.wifiSsid = "ssid";
    cfg.wifiPassword = "pw";
    cfg.backendHost = "host";
    cfg.backendPort = 8000;
    cfg.backendPath = "/ws/device";
    cfg.deviceId = "id";
    cfg.cellId = "cell";
    cfg.deviceToken = "token";
    cfg.ledPwmMin = 100;
    cfg.ledPwmMax = 50;

    auto result = validateRuntimeConfig(cfg);
    TEST_ASSERT_FALSE(result.valid);
    TEST_ASSERT_EQUAL_STRING("led_pwm_min > led_pwm_max", result.message);
}

void test_mixer_max_runtime_zero_fails() {
    RuntimeConfig cfg;
    cfg.wifiSsid = "ssid";
    cfg.wifiPassword = "pw";
    cfg.backendHost = "host";
    cfg.backendPort = 8000;
    cfg.backendPath = "/ws/device";
    cfg.deviceId = "id";
    cfg.cellId = "cell";
    cfg.deviceToken = "token";
    cfg.mixerMaxRuntimeS = 0;

    auto result = validateRuntimeConfig(cfg);
    TEST_ASSERT_FALSE(result.valid);
    TEST_ASSERT_EQUAL_STRING("mixer_max_runtime_s must be > 0", result.message);
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_valid_config_passes);
    RUN_TEST(test_blank_ssid_fails);
    RUN_TEST(test_blank_wifi_password_fails);
    RUN_TEST(test_blank_backend_host_fails);
    RUN_TEST(test_blank_device_id_fails);
    RUN_TEST(test_blank_cell_id_fails);
    RUN_TEST(test_blank_device_token_fails);
    RUN_TEST(test_zero_backend_port_fails);
    RUN_TEST(test_backend_path_not_starting_with_slash_fails);
    RUN_TEST(test_device_id_too_long_fails);
    RUN_TEST(test_cell_id_too_long_fails);
    RUN_TEST(test_led_pwm_min_greater_than_max_fails);
    RUN_TEST(test_mixer_max_runtime_zero_fails);
    return UNITY_END();
}
