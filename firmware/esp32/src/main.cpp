#include <Arduino.h>

#include "BoardConfig.h"
#include "ConfigValidation.h"
#include "config/ConfigStore.h"
#include "provisioning/SerialProvisioner.h"

#if __has_include("BuildSecrets.h")
#include "BuildSecrets.h"
#endif

#ifndef BIOVOLT_WIFI_SSID
#define BIOVOLT_WIFI_SSID ""
#define BIOVOLT_WIFI_PASSWORD ""
#define BIOVOLT_BACKEND_HOST ""
#define BIOVOLT_DEVICE_ID "biovolt-01"
#define BIOVOLT_CELL_ID "cell-a"
#define BIOVOLT_DEVICE_TOKEN ""
#endif

namespace {
ConfigStore configStore;
RuntimeConfig activeConfig;
SerialProvisioner provisioner;

RuntimeConfig buildFallbackConfig() {
  RuntimeConfig config;
  config.wifiSsid = BIOVOLT_WIFI_SSID;
  config.wifiPassword = BIOVOLT_WIFI_PASSWORD;
  config.backendHost = BIOVOLT_BACKEND_HOST;
  config.deviceId = BIOVOLT_DEVICE_ID;
  config.cellId = BIOVOLT_CELL_ID;
  config.deviceToken = BIOVOLT_DEVICE_TOKEN;
  return config;
}

void setActuatorsSafe() {
  pinMode(BoardConfig::kProbeLed680Pin, OUTPUT);
  pinMode(BoardConfig::kGrowLedPwmPin, OUTPUT);
  pinMode(BoardConfig::kMixerPin, OUTPUT);
  digitalWrite(BoardConfig::kProbeLed680Pin, LOW);
  digitalWrite(BoardConfig::kGrowLedPwmPin, LOW);
  digitalWrite(BoardConfig::kMixerPin, LOW);
}
}  // namespace

void setup() {
  Serial.begin(115200);
  delay(50);
  Serial.println("BioVolt firmware boot");

  setActuatorsSafe();
  const RuntimeConfig fallback = buildFallbackConfig();
  configStore.begin();
  activeConfig = configStore.load(fallback);
  provisioner.begin(activeConfig, configStore);

  if (!validateRuntimeConfig(activeConfig).valid) {
    Serial.println("Configuration invalid; actuators remain off and serial provisioning is available");
    return;
  }

  // Network, telemetry, and FreeRTOS runtime start in later firmware modules.
  Serial.println("Configuration loaded for this boot");
}

void loop() {
  provisioner.poll();
  vTaskDelay(pdMS_TO_TICKS(10));
}
