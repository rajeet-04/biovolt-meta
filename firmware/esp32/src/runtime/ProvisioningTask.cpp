#include "ProvisioningTask.h"

void provisioningTaskEntry(void* context) {
  auto* ctx = static_cast<ProvisioningTaskContext*>(context);
  for (;;) {
    if (ctx && ctx->provisioner) ctx->provisioner->poll();
    vTaskDelay(pdMS_TO_TICKS(20));
  }
}
