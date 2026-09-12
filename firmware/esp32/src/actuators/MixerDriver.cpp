#include "MixerDriver.h"

#include <Arduino.h>

#include "BoardConfig.h"

void MixerDriver::begin() {
  digitalWrite(BoardConfig::kMixerPin, LOW);
  pinMode(BoardConfig::kMixerPin, OUTPUT);
  on_ = false;
}

void MixerDriver::write(bool on) {
  digitalWrite(BoardConfig::kMixerPin, on ? HIGH : LOW);
  on_ = on;
}

bool MixerDriver::isOn() const { return on_; }
