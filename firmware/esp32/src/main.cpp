#include <Arduino.h>

#include "BoardConfig.h"
#include "ConfigValidation.h"
#include "config/ConfigStore.h"
#include "provisioning/SerialProvisioner.h"
#include "sensors/SensorManager.h"
#include "actuators/ActuatorController.h"
#include "runtime/ActuatorTask.h"
#include "runtime/ControlTask.h"
#include "runtime/ProvisioningTask.h"
#include "runtime/RuntimeStateStore.h"
#include "runtime/SensorTask.h"

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
SensorManager sensorManager;
GrowLightDriver growLight;
MixerDriver mixer;
SafetyPolicy safetyPolicy({});
ActuatorController actuatorController(growLight, mixer, safetyPolicy);
RuntimeStateStore runtimeState;
QueueHandle_t actuatorQueue = nullptr;
SensorTaskContext sensorTaskContext{&sensorManager, &runtimeState};
ControlTaskContext controlTaskContext{&runtimeState, nullptr};
ActuatorTaskContext actuatorTaskContext{&actuatorController, &runtimeState, nullptr};
ProvisioningTaskContext provisioningTaskContext{&provisioner};

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
  safetyPolicy.setLimits(SafetyLimits{activeConfig.ledPwmMin, activeConfig.ledPwmMax,
                                      static_cast<uint32_t>(activeConfig.mixerMaxRuntimeS) * 1000U,
                                      static_cast<uint32_t>(activeConfig.mixerCooldownS) * 1000U});
  actuatorController.begin();
  sensorManager.begin();
  const bool stateReady = runtimeState.begin();
  actuatorQueue = xQueueCreate(1, sizeof(ActuatorRequest));
  controlTaskContext.actuatorQueue = actuatorQueue;
  actuatorTaskContext.actuatorQueue = actuatorQueue;

  if (!validateRuntimeConfig(activeConfig).valid) {
    Serial.println("Configuration invalid; actuators remain off and serial provisioning is available");
  }

  if (!stateReady || !actuatorQueue) {
    Serial.println("Runtime state or actuator queue unavailable; outputs remain safe");
    setActuatorsSafe();
    return;
  }
  const BaseType_t sensorTask = xTaskCreatePinnedToCore(sensorTaskEntry, "sensor", 4096,
                                                         &sensorTaskContext, 3, nullptr, 1);
  const BaseType_t controlTask = xTaskCreatePinnedToCore(controlTaskEntry, "control", 3072,
                                                          &controlTaskContext, 3, nullptr, 1);
  const BaseType_t actuatorTask = xTaskCreatePinnedToCore(actuatorTaskEntry, "actuator", 3072,
                                                           &actuatorTaskContext, 3, nullptr, 1);
  const BaseType_t provisioningTask = xTaskCreate(provisioningTaskEntry, "provision", 3072,
                                                  &provisioningTaskContext, 1, nullptr);
  if (sensorTask != pdPASS || controlTask != pdPASS || actuatorTask != pdPASS || provisioningTask != pdPASS) {
    Serial.println("Runtime task creation failed; outputs remain safe");
    setActuatorsSafe();
  }
}

void loop() {
  vTaskDelay(pdMS_TO_TICKS(1000));
}
