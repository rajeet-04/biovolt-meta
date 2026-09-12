#include <cstring>
#include <unity.h>

#include "CommandParser.h"

namespace {
const char* base =
    "{\"schema_version\":\"device-command.v1\",\"command_id\":\"7b0a82c6-55c6-4af2-8aac-8dbf93ee3a17\","
    "\"device_id\":\"biovolt-01\",\"experiment_id\":null,\"issued_at\":\"2026-08-23T13:10:00Z\","
    "\"expires_at\":\"2026-08-23T13:10:10Z\",\"ttl_ms\":10000,";

ParseCommandResult parse(const char* suffix) {
  std::string payload = std::string(base) + suffix;
  payload += "}";
  return parseDeviceCommand(payload.c_str(), payload.size());
}
}  // namespace

void test_all_command_kinds_parse() {
  auto mode = parse("\"kind\":\"set_mode\",\"payload\":{\"mode\":\"manual\"}");
  auto pwm = parse("\"kind\":\"set_led_pwm\",\"payload\":{\"pwm\":96}");
  auto mixer = parse("\"kind\":\"set_mixer\",\"payload\":{\"on\":true}");
  auto status = parse("\"kind\":\"request_status\",\"payload\":{}");
  auto stop = parse("\"kind\":\"safe_stop\",\"payload\":{}");
  TEST_ASSERT_TRUE(mode.valid);
  TEST_ASSERT_EQUAL_INT(static_cast<int>(ControlMode::Manual),
                        static_cast<int>(mode.command.requestedMode));
  TEST_ASSERT_TRUE(pwm.valid && pwm.command.requestedPwm == 96);
  TEST_ASSERT_TRUE(mixer.valid && mixer.command.requestedMixerOn);
  TEST_ASSERT_TRUE(status.valid && stop.valid);
}

void test_invalid_command_inputs_are_rejected() {
  auto schema = parse("\"kind\":\"safe_stop\",\"payload\":{}");
  std::string wrong = std::string(base) + "\"schema_version\":\"wrong\",\"kind\":\"safe_stop\",\"payload\":{}}";
  auto badSchema = parseDeviceCommand(wrong.c_str(), wrong.size());
  auto badPwm = parse("\"kind\":\"set_led_pwm\",\"payload\":{\"pwm\":300}");
  auto unknown = parse("\"kind\":\"unknown\",\"payload\":{}");
  TEST_ASSERT_TRUE(schema.valid);
  TEST_ASSERT_FALSE(badSchema.valid);
  TEST_ASSERT_FALSE(badPwm.valid);
  TEST_ASSERT_EQUAL_STRING("unsupported_command", unknown.reasonCode.c_str());
}

void test_queue_item_is_pod_safe_and_round_trips() {
  auto parsed = parse("\"kind\":\"set_mixer\",\"payload\":{\"on\":true}");
  parsed.command.receivedAtMs = 55;
  CommandQueueItem item;
  TEST_ASSERT_TRUE(commandToQueueItem(parsed.command, item));
  const DeviceCommand restored = commandFromQueueItem(item);
  TEST_ASSERT_EQUAL_STRING(parsed.command.commandId.c_str(), restored.commandId.c_str());
  TEST_ASSERT_EQUAL_UINT32(10000, restored.ttlMs);
  TEST_ASSERT_EQUAL_UINT64(55, restored.receivedAtMs);
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_all_command_kinds_parse);
  RUN_TEST(test_invalid_command_inputs_are_rejected);
  RUN_TEST(test_queue_item_is_pod_safe_and_round_trips);
  return UNITY_END();
}
