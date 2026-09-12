#include <unity.h>

#include "CommandPolicy.h"

DeviceCommand command(CommandKind kind) {
  DeviceCommand value;
  value.kind = kind;
  return value;
}

void test_policy_matrix() {
  auto adaptive = command(CommandKind::SetMode);
  adaptive.requestedMode = ControlMode::Adaptive;
  TEST_ASSERT_EQUAL_INT(static_cast<int>(CommandPolicyDecision::PhaseNotAvailable),
                        static_cast<int>(commandPolicy(adaptive, ControlMode::Monitor)));
  TEST_ASSERT_EQUAL_INT(static_cast<int>(CommandPolicyDecision::Allowed),
                        static_cast<int>(commandPolicy(command(CommandKind::SetLedPwm), ControlMode::Manual)));
  TEST_ASSERT_EQUAL_INT(static_cast<int>(CommandPolicyDecision::SafetyRejected),
                        static_cast<int>(commandPolicy(command(CommandKind::SetLedPwm), ControlMode::Monitor)));
  TEST_ASSERT_EQUAL_INT(static_cast<int>(CommandPolicyDecision::Allowed),
                        static_cast<int>(commandPolicy(command(CommandKind::SetMixer), ControlMode::Manual)));
  TEST_ASSERT_EQUAL_INT(static_cast<int>(CommandPolicyDecision::SafetyRejected),
                        static_cast<int>(commandPolicy(command(CommandKind::SetMixer), ControlMode::Passive)));
  TEST_ASSERT_EQUAL_INT(static_cast<int>(CommandPolicyDecision::Allowed),
                        static_cast<int>(commandPolicy(command(CommandKind::SafeStop), ControlMode::Adaptive)));
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_policy_matrix);
  return UNITY_END();
}
