#pragma once
#include <cmath>
#include <cstdint>
#include "ObjectiveWindow.h"
#include "OptimizerTypes.h"

enum class OptimizerState { Inactive, Initialize, Settle, Observe, Hold };
struct OptimizerOutput { OptimizerState state{OptimizerState::Inactive}; bool pwmRequestValid{false}; uint8_t requestedPwm{0}; int8_t direction{0}; const char* holdReason{nullptr}; };
class PAndOOptimizer { public:
 void enable(const PAndOConfig& c,uint64_t now){config_=c; pwm_=c.initialPwm; direction_=1; state_=OptimizerState::Settle; since_=now; window_.clear(); previous_=NAN; enabled_=true; request_=true;}
 void disable(){enabled_=false; state_=OptimizerState::Inactive; window_.clear(); request_=false;}
 OptimizerOutput update(uint64_t now,float voltage,bool valid){ if(!enabled_)return status(); if(state_==OptimizerState::Hold){if(valid){state_=OptimizerState::Settle; since_=now; window_.clear(); holdReason_=nullptr;} return status();} if(valid)window_.addVoltageMv(voltage); if(now-since_<config_.settleMs)return status(); if(window_.validCount()<config_.minimumValidSamples){state_=OptimizerState::Hold; holdReason_="insufficient_valid_data"; return status();} float objective=0; if(!window_.objective(objective))return status(); if(std::isnan(previous_)){previous_=objective; window_.clear(); return perturb(now);} const float change=(objective-previous_)/std::max(std::fabs(previous_),1e-6F); if(change < -config_.objectiveDeadbandFraction)direction_=-direction_; previous_=objective; window_.clear(); return perturb(now); }
 OptimizerOutput status()const{OptimizerOutput out; out.state=state_; out.pwmRequestValid=request_; out.requestedPwm=pwm_; out.direction=direction_; out.holdReason=holdReason_; request_=false; return out;}
 private: OptimizerOutput perturb(uint64_t now){int next=int(pwm_)+direction_*config_.pwmStep; if(next>config_.pwmMax||next<config_.pwmMin){direction_=-direction_; next=int(pwm_)+direction_*config_.pwmStep;} if(next==pwm_){state_=OptimizerState::Hold; holdReason_="pwm_bound"; return status();} pwm_=static_cast<uint8_t>(next); state_=OptimizerState::Settle; since_=now; request_=true; return status();}
 PAndOConfig config_{}; ObjectiveWindow window_{}; OptimizerState state_{OptimizerState::Inactive}; uint64_t since_{0}; float previous_{NAN}; uint8_t pwm_{0}; int8_t direction_{1}; const char* holdReason_{nullptr}; bool enabled_{false}; mutable bool request_{false}; };
