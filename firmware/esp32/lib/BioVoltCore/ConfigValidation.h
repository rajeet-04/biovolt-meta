#pragma once

#include "RuntimeConfig.h"

struct ConfigValidationResult {
  bool valid;
  const char* message;
};

ConfigValidationResult validateRuntimeConfig(const RuntimeConfig& config);
