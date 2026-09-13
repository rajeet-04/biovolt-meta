#include <unity.h>

#include "CommandDedupe.h"

DeviceAck ack(const char* id) {
  DeviceAck result;
  result.commandId = id;
  result.deviceId = "biovolt-01";
  result.status = AckStatus::Applied;
  return result;
}

void test_unseen_and_found_ack() {
  CommandDedupe cache;
  DeviceAck found;
  TEST_ASSERT_FALSE(cache.find("one", found));
  cache.remember("one", ack("one"));
  TEST_ASSERT_TRUE(cache.find("one", found));
  TEST_ASSERT_EQUAL_STRING("one", found.commandId.c_str());
}

void test_fifo_capacity_evicts_oldest() {
  CommandDedupe cache;
  for (size_t index = 0; index < CommandDedupe::kCapacity; ++index) {
    cache.remember(std::to_string(index), ack(std::to_string(index).c_str()));
  }
  cache.remember("new", ack("new"));
  DeviceAck found;
  TEST_ASSERT_FALSE(cache.find("0", found));
  TEST_ASSERT_TRUE(cache.find("new", found));
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_unseen_and_found_ack);
  RUN_TEST(test_fifo_capacity_evicts_oldest);
  return UNITY_END();
}
