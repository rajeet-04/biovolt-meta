#pragma once

#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>

#include "../../lib/BioVoltCore/CommandDedupe.h"
#include "../actuators/ActuatorController.h"
#include "../network/DeviceWebSocket.h"
#include "RuntimeStateStore.h"

struct CommandTaskContext {
  ActuatorController* controller;
  RuntimeStateStore* state;
  DeviceWebSocket* websocket;
  QueueHandle_t commandQueue;
};

void commandTaskEntry(void* context);
