#pragma once

#include <Preferences.h>

#include "RuntimeConfig.h"

class ConfigStore {
 public:
  bool begin();
  RuntimeConfig load(const RuntimeConfig& fallback);
  bool save(const RuntimeConfig& config);
  void clear();

 private:
  Preferences preferences_;
  bool started_{false};
};
