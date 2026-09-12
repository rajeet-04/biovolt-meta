#include <unity.h>

#include "SafetyPolicy.h"

void setUp() {}
void tearDown() {}

void test_pwm_is_clamped_to_limits() {
  SafetyPolicy policy({10, 200, 10000, 60000});
  TEST_ASSERT_EQUAL_UINT8(10, policy.clampPwm(-1));
  TEST_ASSERT_EQUAL_UINT8(100, policy.clampPwm(100));
  TEST_ASSERT_EQUAL_UINT8(200, policy.clampPwm(255));
}

void test_mixer_runtime_and_cooldown_are_enforced() {
  SafetyPolicy policy({0, 255, 10000, 60000});
  TEST_ASSERT_TRUE(policy.canStartMixer(1000));
  policy.noteMixerStarted(1000);
  TEST_ASSERT_FALSE(policy.mixerMustStop(10999));
  TEST_ASSERT_TRUE(policy.mixerMustStop(11000));
  policy.noteMixerStopped(11000);
  TEST_ASSERT_FALSE(policy.canStartMixer(70999));
  TEST_ASSERT_TRUE(policy.canStartMixer(71000));
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_pwm_is_clamped_to_limits);
  RUN_TEST(test_mixer_runtime_and_cooldown_are_enforced);
  return UNITY_END();
}
