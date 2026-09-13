#pragma once

#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>

#include "ControlBaseline.h"
#include "RuntimeStateStore.h"

struct ControlTaskContext {
  RuntimeStateStore* state;
  QueueHandle_t actuatorQueue;
};

void controlTaskEntry(void* context);
