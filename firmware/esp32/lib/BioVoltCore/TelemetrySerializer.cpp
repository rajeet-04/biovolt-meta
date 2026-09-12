#include "TelemetrySerializer.h"

#include <ArduinoJson.h>

namespace {
const char* controlModeName(ControlMode mode) {
  switch (mode) {
    case ControlMode::Passive:
      return "passive";
    case ControlMode::Adaptive:
      return "adaptive";
    case ControlMode::Manual:
      return "manual";
    case ControlMode::Monitor:
    default:
      return "monitor";
  }
}
}  // namespace

bool TelemetrySerializer::serialize(const TelemetryEnvelope& envelope, char* output,
                                    size_t outputSize, size_t& written) const {
  written = 0;
  if (!output || outputSize == 0 || !envelope.deviceId || !envelope.cellId) return false;

  StaticJsonDocument<kJsonCapacity> document;
  document["schema_version"] = 1;
  document["device_id"] = envelope.deviceId;
  document["sequence"] = envelope.sequence;
  document["uptime_ms"] = envelope.uptimeMs;
  document["cell_id"] = envelope.cellId;

  const SensorSnapshot& sensors = envelope.runtime.sensors.snapshot;
  JsonObject electrical = document.createNestedObject("electrical");
  if (sensors.bpvVoltageMv.valid) electrical["bpv_voltage_mv"] = sensors.bpvVoltageMv.value;
  else electrical["bpv_voltage_mv"] = nullptr;
  if (sensors.bpvAdcRaw.valid) electrical["bpv_adc_raw"] = sensors.bpvAdcRaw.value;
  else electrical["bpv_adc_raw"] = nullptr;

  JsonObject optical = document.createNestedObject("optical");
  if (sensors.bpw34Raw.valid) optical["bpw34_raw"] = sensors.bpw34Raw.value;
  else optical["bpw34_raw"] = nullptr;
  if (sensors.bpw34VoltageMv.valid) optical["bpw34_voltage_mv"] = sensors.bpw34VoltageMv.value;
  else optical["bpw34_voltage_mv"] = nullptr;
  optical["led_680_enabled"] = sensors.led680EnabledAtSample;

  JsonObject environment = document.createNestedObject("environment");
  if (sensors.temperatureC.valid) environment["temperature_c"] = sensors.temperatureC.value;
  else environment["temperature_c"] = nullptr;
  if (sensors.lux.valid) environment["lux"] = sensors.lux.value;
  else environment["lux"] = nullptr;

  JsonObject actuators = document.createNestedObject("actuators");
  actuators["grow_led_pwm"] = envelope.runtime.actuators.growLedPwm;
  actuators["mixer_on"] = envelope.runtime.actuators.mixerOn;

  JsonObject control = document.createNestedObject("control");
  control["mode"] = controlModeName(envelope.runtime.control.mode);
  control["optimizer_direction"] = envelope.runtime.control.optimizerDirection;

  JsonObject health = document.createNestedObject("health");
  health["ads1115_ok"] = envelope.runtime.sensors.health.ads1115Ok;
  health["bpw34_ok"] = envelope.runtime.sensors.health.bpw34Ok;
  health["temperature_ok"] = envelope.runtime.sensors.health.temperatureOk;
  health["light_sensor_ok"] = envelope.runtime.sensors.health.lightSensorOk;

  if (document.overflowed()) return false;
  written = serializeJson(document, output, outputSize);
  return written > 0 && written < outputSize;
}

