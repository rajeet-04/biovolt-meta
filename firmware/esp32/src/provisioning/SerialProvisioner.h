#pragma once

#include <Arduino.h>

#include "../config/ConfigStore.h"

class SerialProvisioner {
 public:
  void begin(const RuntimeConfig& activeConfig, ConfigStore& store);
  void poll();

 private:
  static constexpr size_t kMaxLineLength = 256;

  void handleLine(const String& line);
  void showDraft() const;
  void showStatus() const;
  bool setValue(const String& field, const String& value);
  bool isPending() const;

  RuntimeConfig activeConfig_;
  RuntimeConfig draftConfig_;
  ConfigStore* store_{nullptr};
  String input_;
};
