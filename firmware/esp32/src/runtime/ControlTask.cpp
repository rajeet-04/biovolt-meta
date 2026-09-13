#include "ControlTask.h"

void controlTaskEntry(void* context) {
  auto* ctx = static_cast<ControlTaskContext*>(context);
  TickType_t lastWake = xTaskGetTickCount();
  for (;;) {
    const RuntimeSnapshot snapshot = ctx && ctx->state ? ctx->state->snapshot() : RuntimeSnapshot{};
    if (ctx && ctx->state && snapshot.control.mode == ControlMode::Monitor) {
      ctx->state->updateControl(phase3ControlState());
    }
    if (ctx && ctx->actuatorQueue && snapshot.control.mode == ControlMode::Monitor) {
      const ActuatorRequest request = phase3DefaultActuatorRequest();
      xQueueOverwrite(ctx->actuatorQueue, &request);
    }
    vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(500));
  }
}
