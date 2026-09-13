#pragma once

#include <array>
#include <cstddef>
#include <string>

#include "AckModel.h"

class CommandDedupe {
 public:
  static constexpr size_t kCapacity = 32;

  bool find(const std::string& commandId, DeviceAck& ack) const {
    for (const Entry& entry : entries_) {
      if (entry.used && entry.commandId == commandId) {
        ack = entry.ack;
        return true;
      }
    }
    return false;
  }

  void remember(const std::string& commandId, const DeviceAck& terminalAck) {
    entries_[next_].used = true;
    entries_[next_].commandId = commandId;
    entries_[next_].ack = terminalAck;
    next_ = (next_ + 1) % kCapacity;
  }

 private:
  struct Entry {
    bool used{false};
    std::string commandId;
    DeviceAck ack;
  };
  std::array<Entry, kCapacity> entries_{};
  size_t next_{0};
};
