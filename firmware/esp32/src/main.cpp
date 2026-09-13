#include <Arduino.h>

void setup() {
  Serial.begin(115200);
  delay(50);
  Serial.println("BioVolt firmware boot");
}

void loop() {
  vTaskDelay(pdMS_TO_TICKS(1000));
}
