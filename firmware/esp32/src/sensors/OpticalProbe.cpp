#include "OpticalProbe.h"

#include <Arduino.h>

#include "BoardConfig.h"

OpticalProbe::OpticalProbe(Ads1115Sampler& adc) : adc_(adc) {}

void OpticalProbe::begin() {
  digitalWrite(BoardConfig::kProbeLed680Pin, LOW);
  pinMode(BoardConfig::kProbeLed680Pin, OUTPUT);
}

OpticalSample OpticalProbe::sample() {
  OpticalSample result;
  digitalWrite(BoardConfig::kProbeLed680Pin, HIGH);
  vTaskDelay(pdMS_TO_TICKS(20));
  result.receiver = adc_.readOptical();
  result.ledEnabledAtSample = result.receiver.valid;
  digitalWrite(BoardConfig::kProbeLed680Pin, LOW);
  return result;
}
