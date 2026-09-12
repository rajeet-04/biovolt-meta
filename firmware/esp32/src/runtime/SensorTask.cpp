#include "SensorTask.h"

#include <Arduino.h>
#include <esp_timer.h>

void sensorTaskEntry(void* context) {
  auto* ctx = static_cast<SensorTaskContext*>(context);
  TickType_t lastWake = xTaskGetTickCount();
  uint32_t cycles = 0;
  for (;;) {
    const uint64_t nowMs = esp_timer_get_time() / 1000ULL;
    if (ctx && ctx->sensors && ctx->state) ctx->state->updateSensors(ctx->sensors->sample(nowMs), nowMs);
#ifdef BIOVOLT_DEBUG_TASK_TIMING
    if (++cycles % 20 == 0) Serial.printf("sensor_task cycle=%lu\n", static_cast<unsigned long>(cycles));
#endif
    vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(500));
  }
}
