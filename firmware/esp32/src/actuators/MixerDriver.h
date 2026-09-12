#pragma once

class MixerDriver {
 public:
  void begin();
  void write(bool on);
  bool isOn() const;

 private:
  bool on_{false};
};
