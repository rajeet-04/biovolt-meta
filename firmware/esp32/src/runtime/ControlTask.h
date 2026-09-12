#pragma once

#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>

#include "ControlBaseline.h"
#include "RuntimeStateStore.h"
#include "PAndOOptimizer.h"

struct ControlTaskContext {
  RuntimeStateStore* state;
  QueueHandle_t actuatorQueue;
  PAndOOptimizer* optimizer;
};

void controlTaskEntry(void* context);
