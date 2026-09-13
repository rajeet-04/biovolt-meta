#include "ControlTask.h"

void controlTaskEntry(void* context) {
  auto* ctx = static_cast<ControlTaskContext*>(context);
  TickType_t lastWake = xTaskGetTickCount();
  for (;;) {
    const RuntimeSnapshot snapshot = ctx && ctx->state ? ctx->state->snapshot() : RuntimeSnapshot{};
    if (ctx && ctx->state && snapshot.control.mode == ControlMode::Monitor) {
      ctx->state->updateControl(phase3ControlState());
    }
    if (ctx && ctx->state && ctx->optimizer && snapshot.control.mode == ControlMode::Adaptive) {
      const auto& bpv = snapshot.sensors.snapshot.bpvVoltageMv;
      const OptimizerOutput output = ctx->optimizer->update(
          static_cast<uint64_t>(xTaskGetTickCount()) * portTICK_PERIOD_MS,
          bpv.value, bpv.valid && snapshot.sensors.health.ads1115Ok);
      ControlState control;
      control.mode = ControlMode::Adaptive;
      control.optimizerDirection = output.direction;
      ctx->state->updateControl(control);
      if (output.pwmRequestValid && ctx->actuatorQueue) {
        ActuatorRequest request{};
        request.growLedPwm = output.requestedPwm;
        request.mixerOn = snapshot.actuators.mixerOn;
        xQueueOverwrite(ctx->actuatorQueue, &request);
      }
    }
    if (ctx && ctx->actuatorQueue && snapshot.control.mode == ControlMode::Monitor) {
      const ActuatorRequest request = phase3DefaultActuatorRequest();
      xQueueOverwrite(ctx->actuatorQueue, &request);
    }
    vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(500));
  }
}
