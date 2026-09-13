#pragma once

#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

#include "../sensors/SensorManager.h"
#include "RuntimeStateStore.h"

struct SensorTaskContext {
  SensorManager* sensors;
  RuntimeStateStore* state;
};

void sensorTaskEntry(void* context);
