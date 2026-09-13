#include <unity.h>
#include "PAndOOptimizer.h"
#include "ObjectiveWindow.h"
#include "OptimizerTypes.h"
void test_validation(){TEST_ASSERT_TRUE(validatePAndOConfig(PAndOConfig{}).valid); auto c=PAndOConfig{}; c.settleMs=1; TEST_ASSERT_FALSE(validatePAndOConfig(c).valid);}
void test_window(){ObjectiveWindow w; w.addVoltageMv(1);w.addVoltageMv(3);w.addVoltageMv(2);float o=0;TEST_ASSERT_TRUE(w.objective(o));TEST_ASSERT_FLOAT_WITHIN(0.01F,4,o);TEST_ASSERT_FALSE(w.addVoltageMv(NAN));}
void test_optimizer(){PAndOOptimizer o; PAndOConfig c; c.settleMs=500;c.minimumValidSamples=1;o.enable(c,0);auto first=o.status();TEST_ASSERT_TRUE(first.pwmRequestValid);auto early=o.update(100,10,true);TEST_ASSERT_FALSE(early.pwmRequestValid);auto next=o.update(1001,10,true);TEST_ASSERT_TRUE(next.pwmRequestValid);TEST_ASSERT_LESS_OR_EQUAL(255,next.requestedPwm);}
int main(int, char**) { UNITY_BEGIN(); RUN_TEST(test_validation); RUN_TEST(test_window); RUN_TEST(test_optimizer); return UNITY_END(); }
