#include <unity.h>
#include "SensorTypes.h"
#include "RuntimeTypes.h"

void setUp() {}
void tearDown() {}

void test_sensor_value_default_is_invalid() {
  SensorValue<float> v;
  TEST_ASSERT_FALSE(v.valid);
  TEST_ASSERT_EQUAL_FLOAT(0.0f, v.value);

  SensorValue<int16_t> i;
  TEST_ASSERT_FALSE(i.valid);
  TEST_ASSERT_EQUAL_INT16(0, i.value);
}

void test_sensor_snapshot_defaults_invalid() {
  SensorSnapshot s;
  TEST_ASSERT_FALSE(s.bpvVoltageMv.valid);
  TEST_ASSERT_FALSE(s.bpvAdcRaw.valid);
  TEST_ASSERT_FALSE(s.bpw34VoltageMv.valid);
  TEST_ASSERT_FALSE(s.bpw34Raw.valid);
  TEST_ASSERT_FALSE(s.led680EnabledAtSample);
  TEST_ASSERT_FALSE(s.temperatureC.valid);
  TEST_ASSERT_FALSE(s.lux.valid);
}

void test_sensor_frame_health_defaults_false() {
  SensorFrame frame;
  TEST_ASSERT_FALSE(frame.health.ads1115Ok);
  TEST_ASSERT_FALSE(frame.health.bpw34Ok);
  TEST_ASSERT_FALSE(frame.health.temperatureOk);
  TEST_ASSERT_FALSE(frame.health.lightSensorOk);
}

void test_analog_sample_defaults_invalid() {
  AnalogSample sample;
  TEST_ASSERT_FALSE(sample.valid);
  TEST_ASSERT_EQUAL_INT16(0, sample.raw);
  TEST_ASSERT_EQUAL_FLOAT(0.0F, sample.millivolts);
}

void test_actuator_state_defaults_off() {
  ActuatorState a;
  TEST_ASSERT_EQUAL_UINT8(0, a.growLedPwm);
  TEST_ASSERT_FALSE(a.mixerOn);
}

void test_control_mode_monitor_is_first() {
  TEST_ASSERT_EQUAL_INT(0, static_cast<int>(ControlMode::Monitor));
}

void test_control_state_defaults_monitor_zero() {
  ControlState c;
  TEST_ASSERT_EQUAL(ControlMode::Monitor, c.mode);
  TEST_ASSERT_EQUAL_INT8(0, c.optimizerDirection);
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_sensor_value_default_is_invalid);
  RUN_TEST(test_sensor_snapshot_defaults_invalid);
  RUN_TEST(test_sensor_frame_health_defaults_false);
  RUN_TEST(test_analog_sample_defaults_invalid);
  RUN_TEST(test_actuator_state_defaults_off);
  RUN_TEST(test_control_mode_monitor_is_first);
  RUN_TEST(test_control_state_defaults_monitor_zero);
  return UNITY_END();
}
