#pragma once

#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>

#include "../actuators/ActuatorController.h"
#include "RuntimeStateStore.h"

struct ActuatorTaskContext {
  ActuatorController* controller;
  RuntimeStateStore* state;
  QueueHandle_t actuatorQueue;
};

void actuatorTaskEntry(void* context);
