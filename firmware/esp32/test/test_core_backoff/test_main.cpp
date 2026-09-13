#include <unity.h>
#include "Backoff.h"

void setUp() {}
void tearDown() {}

void test_reconnect_delay_table() {
  const uint32_t expected[] = {1000, 2000, 4000, 8000, 10000, 10000, 10000};
  for (uint32_t attempt = 0; attempt < 7; ++attempt) {
    TEST_ASSERT_EQUAL_UINT32(expected[attempt], reconnectDelayMs(attempt));
  }
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_reconnect_delay_table);
  return UNITY_END();
}
