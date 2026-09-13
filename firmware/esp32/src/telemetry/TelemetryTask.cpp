#include "TelemetryTask.h"

#include <Arduino.h>
#include <esp_timer.h>

void telemetryTaskEntry(void* context) {
  auto* ctx = static_cast<TelemetryTaskContext*>(context);
  TelemetrySerializer serializer;
  char payload[TelemetrySerializer::kJsonCapacity];
  uint32_t sequence = 0;
  uint64_t nextTelemetryMs = esp_timer_get_time() / 1000ULL + 500;

  for (;;) {
    const uint64_t nowMs = esp_timer_get_time() / 1000ULL;
    if (ctx && ctx->network && ctx->websocket) {
      ctx->network->poll(nowMs);
      ctx->websocket->poll(nowMs, ctx->network->connected());
    }
    if (nowMs >= nextTelemetryMs) {
      const uint64_t missed = ((nowMs - nextTelemetryMs) / 500ULL) + 1ULL;
      sequence += static_cast<uint32_t>(missed);
      nextTelemetryMs += missed * 500ULL;
      if (ctx && ctx->state && ctx->config && ctx->websocket) {
        TelemetryEnvelope envelope;
        envelope.deviceId = ctx->config->deviceId.c_str();
        envelope.cellId = ctx->config->cellId.c_str();
        envelope.sequence = sequence;
        envelope.uptimeMs = nowMs;
        envelope.runtime = ctx->state->snapshot();
        size_t written = 0;
        if (serializer.serialize(envelope, payload, sizeof(payload), written) &&
            ctx->websocket->connected()) {
          ctx->websocket->sendText(payload, written);
        }
      }
    }
    vTaskDelay(pdMS_TO_TICKS(20));
  }
}
