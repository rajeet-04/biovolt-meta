#include <unity.h>

#include "ControlBaseline.h"

void setUp() {}
void tearDown() {}

void test_phase3_stays_monitor_and_safe() {
  const auto control = phase3ControlState();
  const auto request = phase3DefaultActuatorRequest();
  TEST_ASSERT_EQUAL(ControlMode::Monitor, control.mode);
  TEST_ASSERT_EQUAL_INT8(0, control.optimizerDirection);
  TEST_ASSERT_EQUAL_INT(0, request.growLedPwm);
  TEST_ASSERT_FALSE(request.mixerOn);
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_phase3_stays_monitor_and_safe);
  return UNITY_END();
}
