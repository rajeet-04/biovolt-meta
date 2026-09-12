#pragma once

#include "../provisioning/SerialProvisioner.h"

struct ProvisioningTaskContext {
  SerialProvisioner* provisioner;
};

void provisioningTaskEntry(void* context);
