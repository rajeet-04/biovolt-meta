#include <ArduinoJson.h>
#include <unity.h>

#include "AckSerializer.h"

void test_applied_ack_has_exact_contract_keys() {
  DeviceAck ack;
  ack.commandId = "7b0a82c6-55c6-4af2-8aac-8dbf93ee3a17";
  ack.deviceId = "biovolt-01";
  ack.status = AckStatus::Applied;
  ack.uptimeMs = 153400;
  ack.appliedMode = ControlMode::Manual;
  ack.appliedState = {96, false};
  ack.includeAppliedState = true;
  char output[AckSerializer::kJsonCapacity];
  size_t written = 0;
  TEST_ASSERT_TRUE(AckSerializer().serialize(ack, output, sizeof(output), written));
  StaticJsonDocument<AckSerializer::kJsonCapacity> document;
  TEST_ASSERT_FALSE(deserializeJson(document, output));
  TEST_ASSERT_EQUAL_STRING("device-ack.v1", document["schema_version"]);
  TEST_ASSERT_EQUAL_STRING("applied", document["status"]);
  TEST_ASSERT_EQUAL_STRING("manual", document["applied_state"]["mode"]);
  TEST_ASSERT_EQUAL(8, document.size());
  TEST_ASSERT_FALSE(document.containsKey("token"));
}

void test_rejected_ack_contains_reason_and_null_state() {
  DeviceAck ack;
  ack.commandId = "7b0a82c6-55c6-4af2-8aac-8dbf93ee3a17";
  ack.deviceId = "biovolt-01";
  ack.status = AckStatus::Rejected;
  ack.reasonCode = "phase_not_available";
  ack.message = "adaptive mode is unavailable";
  char output[AckSerializer::kJsonCapacity];
  size_t written = 0;
  TEST_ASSERT_TRUE(AckSerializer().serialize(ack, output, sizeof(output), written));
  StaticJsonDocument<AckSerializer::kJsonCapacity> document;
  TEST_ASSERT_FALSE(deserializeJson(document, output));
  TEST_ASSERT_EQUAL_STRING("phase_not_available", document["reason_code"]);
  TEST_ASSERT_TRUE(document["applied_state"].isNull());
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_applied_ack_has_exact_contract_keys);
  RUN_TEST(test_rejected_ack_contains_reason_and_null_state);
  return UNITY_END();
}
