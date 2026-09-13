#include "ActuatorTask.h"

#include <Arduino.h>
#include <esp_timer.h>

void actuatorTaskEntry(void* context) {
  auto* ctx = static_cast<ActuatorTaskContext*>(context);
  ActuatorRequest request;
  for (;;) {
    const uint64_t nowMs = esp_timer_get_time() / 1000ULL;
    if (ctx && ctx->actuatorQueue && xQueueReceive(ctx->actuatorQueue, &request, pdMS_TO_TICKS(100)) == pdTRUE) {
      const RuntimeSnapshot snapshot = ctx->state ? ctx->state->snapshot() : RuntimeSnapshot{};
      if (ctx->controller && snapshot.control.mode == ControlMode::Monitor) {
        ctx->controller->apply(request, nowMs);
      }
    }
    if (ctx && ctx->controller) {
      const ActuatorState applied = ctx->controller->enforceTimeouts(nowMs);
      if (ctx->state) ctx->state->updateActuators(applied);
    }
  }
}
