#include <Arduino.h>

#include "BoardConfig.h"
#include "ConfigValidation.h"
#include "config/ConfigStore.h"
#include "provisioning/SerialProvisioner.h"
#include "sensors/SensorManager.h"
#include "actuators/ActuatorController.h"
#include "runtime/ActuatorTask.h"
#include "runtime/ControlTask.h"
#include "runtime/CommandTask.h"
#include "runtime/ProvisioningTask.h"
#include "runtime/RuntimeStateStore.h"
#include "runtime/SensorTask.h"
#include "network/DeviceWebSocket.h"
#include "network/NetworkManager.h"
#include "telemetry/TelemetryTask.h"
#include "PAndOOptimizer.h"

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
PAndOOptimizer adaptiveOptimizer;
NetworkManager networkManager;
DeviceWebSocket deviceWebSocket;
QueueHandle_t actuatorQueue = nullptr;
QueueHandle_t commandQueue = nullptr;
SensorTaskContext sensorTaskContext{&sensorManager, &runtimeState};
ControlTaskContext controlTaskContext{&runtimeState, nullptr, &adaptiveOptimizer};
ActuatorTaskContext actuatorTaskContext{&actuatorController, &runtimeState, nullptr};
CommandTaskContext commandTaskContext{&actuatorController, &runtimeState, &deviceWebSocket, nullptr};
ProvisioningTaskContext provisioningTaskContext{&provisioner};
TelemetryTaskContext telemetryTaskContext{&runtimeState, &networkManager, &deviceWebSocket, &activeConfig};

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
  networkManager.begin(activeConfig);
  deviceWebSocket.begin(activeConfig);
  safetyPolicy.setLimits(SafetyLimits{activeConfig.ledPwmMin, activeConfig.ledPwmMax,
                                      static_cast<uint32_t>(activeConfig.mixerMaxRuntimeS) * 1000U,
                                      static_cast<uint32_t>(activeConfig.mixerCooldownS) * 1000U});
  actuatorController.begin();
  sensorManager.begin();
  const bool stateReady = runtimeState.begin();
  actuatorQueue = xQueueCreate(1, sizeof(ActuatorRequest));
  commandQueue = xQueueCreate(8, sizeof(CommandQueueItem));
  controlTaskContext.actuatorQueue = actuatorQueue;
  actuatorTaskContext.actuatorQueue = actuatorQueue;
  commandTaskContext.commandQueue = commandQueue;
  deviceWebSocket.setCommandQueue(commandQueue);

  if (!validateRuntimeConfig(activeConfig).valid) {
    Serial.println("Configuration invalid; actuators remain off and serial provisioning is available");
  }

  if (!stateReady || !actuatorQueue || !commandQueue) {
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
  const BaseType_t commandTask = xTaskCreatePinnedToCore(commandTaskEntry, "command", 4096,
                                                          &commandTaskContext, 3, nullptr, 1);
  const BaseType_t provisioningTask = xTaskCreate(provisioningTaskEntry, "provision", 3072,
                                                  &provisioningTaskContext, 1, nullptr);
  const BaseType_t telemetryTask = xTaskCreatePinnedToCore(telemetryTaskEntry, "telemetry", 6144,
                                                            &telemetryTaskContext, 2, nullptr, 1);
  if (sensorTask != pdPASS || controlTask != pdPASS || actuatorTask != pdPASS ||
      commandTask != pdPASS ||
      provisioningTask != pdPASS || telemetryTask != pdPASS) {
    Serial.println("Runtime task creation failed; outputs remain safe");
    setActuatorsSafe();
  }
}

void loop() {
  vTaskDelay(pdMS_TO_TICKS(1000));
}
