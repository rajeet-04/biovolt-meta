#include "SensorManager.h"

#include <Arduino.h>

void SensorManager::begin() {
  adc_.begin();
  temperature_.begin();
  light_.begin();
  optical_.begin();
}

SensorFrame SensorManager::sample(uint64_t nowMs) {
  SensorFrame frame;
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
}
