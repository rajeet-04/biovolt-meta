#pragma once

#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

#include "../../lib/BioVoltCore/TelemetrySerializer.h"
#include "../config/ConfigStore.h"
#include "../network/DeviceWebSocket.h"
#include "../network/NetworkManager.h"
#include "../runtime/RuntimeStateStore.h"

struct TelemetryTaskContext {
  RuntimeStateStore* state;
  NetworkManager* network;
  DeviceWebSocket* websocket;
  const RuntimeConfig* config;
};

void telemetryTaskEntry(void* context);

