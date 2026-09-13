#include "ControlTask.h"

void controlTaskEntry(void* context) {
  auto* ctx = static_cast<ControlTaskContext*>(context);
  TickType_t lastWake = xTaskGetTickCount();
  for (;;) {
    if (ctx && ctx->state) ctx->state->updateControl(phase3ControlState());
    if (ctx && ctx->actuatorQueue) {
      const ActuatorRequest request = phase3DefaultActuatorRequest();
      xQueueOverwrite(ctx->actuatorQueue, &request);
    }
    vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(500));
  }
}
