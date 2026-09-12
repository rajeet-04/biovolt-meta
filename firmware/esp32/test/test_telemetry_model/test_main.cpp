#include <ArduinoJson.h>
#include <unity.h>

#include "TelemetrySerializer.h"

namespace {
char output[TelemetrySerializer::kJsonCapacity];

TelemetryEnvelope envelope() {
  TelemetryEnvelope result{"biovolt-01", "cell-a", 12, 3456, {}};
  result.runtime.sensors.snapshot.bpvVoltageMv = {420.5F, true};
  result.runtime.sensors.snapshot.bpvAdcRaw = {123, true};
  result.runtime.sensors.snapshot.bpw34Raw = {456, true};
  result.runtime.sensors.snapshot.bpw34VoltageMv = {78.9F, true};
  result.runtime.sensors.snapshot.led680EnabledAtSample = true;
  result.runtime.sensors.snapshot.temperatureC = {25.5F, true};
  result.runtime.sensors.snapshot.lux = {99.0F, true};
  result.runtime.sensors.health = {true, true, true, true};
  result.runtime.actuators = {80, false};
  result.runtime.control = {ControlMode::Monitor, 0};
  return result;
}

}  // namespace

void test_exact_top_level_keys() {
  size_t written = 0;
  TEST_ASSERT_TRUE(TelemetrySerializer().serialize(envelope(), output, sizeof(output), written));
  StaticJsonDocument<TelemetrySerializer::kJsonCapacity> document;
  TEST_ASSERT_FALSE(deserializeJson(document, output));
  const char* keys[] = {"schema_version", "device_id", "sequence", "uptime_ms", "cell_id",
                        "electrical", "optical", "environment", "actuators", "control", "health"};
  for (const char* key : keys) TEST_ASSERT_TRUE(document.containsKey(key));
  TEST_ASSERT_EQUAL(11, document.size());
}

void test_exact_nested_keys_and_no_derived_fields() {
  size_t written = 0;
  TEST_ASSERT_TRUE(TelemetrySerializer().serialize(envelope(), output, sizeof(output), written));
  StaticJsonDocument<TelemetrySerializer::kJsonCapacity> document;
  TEST_ASSERT_FALSE(deserializeJson(document, output));
  TEST_ASSERT_TRUE(document["electrical"].containsKey("bpv_voltage_mv"));
  TEST_ASSERT_TRUE(document["electrical"].containsKey("bpv_adc_raw"));
  TEST_ASSERT_TRUE(document["optical"].containsKey("bpw34_raw"));
  TEST_ASSERT_TRUE(document["optical"].containsKey("bpw34_voltage_mv"));
  TEST_ASSERT_TRUE(document["optical"].containsKey("led_680_enabled"));
  TEST_ASSERT_TRUE(document["environment"].containsKey("temperature_c"));
  TEST_ASSERT_TRUE(document["environment"].containsKey("lux"));
  TEST_ASSERT_TRUE(document["actuators"].containsKey("grow_led_pwm"));
  TEST_ASSERT_TRUE(document["actuators"].containsKey("mixer_on"));
  TEST_ASSERT_TRUE(document["control"].containsKey("mode"));
  TEST_ASSERT_TRUE(document["control"].containsKey("optimizer_direction"));
  TEST_ASSERT_TRUE(document["health"].containsKey("ads1115_ok"));
  TEST_ASSERT_FALSE(document.containsKey("current_ua"));
  TEST_ASSERT_FALSE(document.containsKey("power_uw"));
  TEST_ASSERT_FALSE(document.containsKey("od680"));
  TEST_ASSERT_FALSE(document.containsKey("biomass"));
  TEST_ASSERT_FALSE(document.containsKey("co2_biofixed"));
  TEST_ASSERT_FALSE(document.containsKey("cumulative_energy"));
  TEST_ASSERT_FALSE(document.containsKey("timestamp"));
}

void test_invalid_values_are_null_with_false_health() {
  TelemetryEnvelope value = envelope();
  value.runtime.sensors.snapshot.temperatureC.valid = false;
  value.runtime.sensors.snapshot.bpvAdcRaw.valid = false;
  value.runtime.sensors.health.temperatureOk = false;
  value.runtime.sensors.health.ads1115Ok = false;
  size_t written = 0;
  TEST_ASSERT_TRUE(TelemetrySerializer().serialize(value, output, sizeof(output), written));
  StaticJsonDocument<TelemetrySerializer::kJsonCapacity> document;
  TEST_ASSERT_FALSE(deserializeJson(document, output));
  TEST_ASSERT_TRUE(document["environment"]["temperature_c"].isNull());
  TEST_ASSERT_FALSE(document["health"]["temperature_ok"]);
  TEST_ASSERT_TRUE(document["electrical"]["bpv_adc_raw"].isNull());
  TEST_ASSERT_FALSE(document["health"]["ads1115_ok"]);
}

void test_all_fields_fit_capacity() {
  size_t written = 0;
  TEST_ASSERT_TRUE(TelemetrySerializer().serialize(envelope(), output, sizeof(output), written));
  TEST_ASSERT_GREATER_THAN(0, written);
  TEST_ASSERT_LESS_THAN(sizeof(output), written);
}

void test_mode_names_are_contract_values() {
  for (const auto mode : {ControlMode::Monitor, ControlMode::Passive, ControlMode::Adaptive,
                          ControlMode::Manual}) {
    TelemetryEnvelope value = envelope();
    value.runtime.control.mode = mode;
    size_t written = 0;
    TEST_ASSERT_TRUE(TelemetrySerializer().serialize(value, output, sizeof(output), written));
    StaticJsonDocument<TelemetrySerializer::kJsonCapacity> document;
    TEST_ASSERT_FALSE(deserializeJson(document, output));
    TEST_ASSERT_NOT_NULL(document["control"]["mode"]);
  }
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_exact_top_level_keys);
  RUN_TEST(test_exact_nested_keys_and_no_derived_fields);
  RUN_TEST(test_invalid_values_are_null_with_false_health);
  RUN_TEST(test_all_fields_fit_capacity);
  RUN_TEST(test_mode_names_are_contract_values);
  UNITY_END();
}
