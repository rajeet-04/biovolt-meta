#pragma once
#include <cstdint>

struct PAndOConfig { uint8_t initialPwm{64}; uint8_t pwmMin{0}; uint8_t pwmMax{255}; uint8_t pwmStep{4}; uint32_t settleMs{3000}; uint8_t minimumValidSamples{3}; float objectiveDeadbandFraction{0.01F}; };
struct PAndOConfigValidationResult { bool valid; const char* reason; };
inline PAndOConfigValidationResult validatePAndOConfig(const PAndOConfig& c) { if (c.pwmMin >= c.pwmMax) return {false,"invalid_bounds"}; if (c.initialPwm < c.pwmMin || c.initialPwm > c.pwmMax) return {false,"initial_out_of_bounds"}; if (c.pwmStep == 0 || c.pwmStep > 32 || c.pwmStep > c.pwmMax - c.pwmMin) return {false,"invalid_step"}; if (c.settleMs < 500 || c.minimumValidSamples == 0 || c.minimumValidSamples > 9) return {false,"invalid_sampling"}; if (!(c.objectiveDeadbandFraction >= 0.0F && c.objectiveDeadbandFraction <= 0.25F)) return {false,"invalid_deadband"}; return {true,nullptr}; }
