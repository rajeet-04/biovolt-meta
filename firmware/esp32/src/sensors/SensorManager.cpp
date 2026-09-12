#include "SensorManager.h"

#include <Arduino.h>

#ifdef BIOVOLT_SIMULATED_SENSORS
#include <cmath>
#endif

void SensorManager::begin() {
#ifdef BIOVOLT_SIMULATED_SENSORS
  return;
#else
  adc_.begin();
  temperature_.begin();
  light_.begin();
  optical_.begin();
#endif
}

SensorFrame SensorManager::sample(uint64_t nowMs) {
  SensorFrame frame;
#ifdef BIOVOLT_SIMULATED_SENSORS
  const float phase = static_cast<float>(nowMs % 10000ULL) / 10000.0F;
  frame.snapshot.bpvVoltageMv.value = 420.0F + 5.0F * std::sin(phase * 6.2831853F);
  frame.snapshot.bpvVoltageMv.valid = true;
  frame.snapshot.bpvAdcRaw.value = static_cast<int16_t>(1200 + 20 * std::sin(phase * 6.2831853F));
  frame.snapshot.bpvAdcRaw.valid = true;
  frame.snapshot.bpw34VoltageMv.value = 75.0F + 2.0F * std::sin(phase * 12.5663706F);
  frame.snapshot.bpw34VoltageMv.valid = true;
  frame.snapshot.bpw34Raw.value = static_cast<int16_t>(350 + 12 * std::sin(phase * 12.5663706F));
  frame.snapshot.bpw34Raw.valid = true;
  frame.snapshot.temperatureC.value = 25.0F + 0.5F * std::sin(phase * 6.2831853F);
  frame.snapshot.temperatureC.valid = true;
  frame.snapshot.lux.value = 180.0F + 20.0F * std::sin(phase * 6.2831853F);
  frame.snapshot.lux.valid = true;
  frame.health.ads1115Ok = true;
  frame.health.bpw34Ok = true;
  frame.health.temperatureOk = true;
  frame.health.lightSensorOk = true;
  return frame;
#else
  temperature_.poll(nowMs);

  const auto bpv = adc_.readBpv();
  const auto optical = optical_.sample();
  const auto temperature = temperature_.latest();
  const auto lux = light_.readLux();

  frame.snapshot.bpvVoltageMv.value = bpv.millivolts;
  frame.snapshot.bpvVoltageMv.valid = bpv.valid;
  frame.snapshot.bpvAdcRaw.value = bpv.raw;
  frame.snapshot.bpvAdcRaw.valid = bpv.valid;
  frame.snapshot.bpw34VoltageMv.value = optical.receiver.millivolts;
  frame.snapshot.bpw34VoltageMv.valid = optical.receiver.valid;
  frame.snapshot.bpw34Raw.value = optical.receiver.raw;
  frame.snapshot.bpw34Raw.valid = optical.receiver.valid;
  frame.snapshot.led680EnabledAtSample = optical.ledEnabledAtSample;
  frame.snapshot.temperatureC = temperature;
  frame.snapshot.lux = lux;

  frame.health.ads1115Ok = adc_.healthy();
  frame.health.bpw34Ok = optical.receiver.valid;
  frame.health.temperatureOk = temperature.valid;
  frame.health.lightSensorOk = lux.valid;

#ifdef BIOVOLT_SENSOR_DIAGNOSTIC
  static uint64_t lastDiagnosticMs = 0;
  if (nowMs - lastDiagnosticMs >= 1000) {
    lastDiagnosticMs = nowMs;
    Serial.printf("sensor ads=%d bpv_valid=%d optical_valid=%d temp_valid=%d lux_valid=%d\n",
                  frame.health.ads1115Ok, frame.snapshot.bpvVoltageMv.valid,
                  frame.health.bpw34Ok, frame.health.temperatureOk, frame.health.lightSensorOk);
  }
#endif
  return frame;
#endif
}
