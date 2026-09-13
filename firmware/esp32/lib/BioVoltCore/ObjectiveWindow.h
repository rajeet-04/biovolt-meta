#pragma once
#include <algorithm>
#include <cmath>
#include <cstddef>

class ObjectiveWindow { public: static constexpr size_t kMaxSamples = 9; void clear(){count_=0;} bool addVoltageMv(float v){if(!std::isfinite(v)||count_==kMaxSamples)return false; values_[count_++]=v; return true;} size_t validCount()const{return count_;} bool objective(float& out)const{if(!count_)return false; float sorted[kMaxSamples]{}; std::copy(values_,values_+count_,sorted); std::sort(sorted,sorted+count_); const float median=(count_%2)?sorted[count_/2]:(sorted[count_/2-1]+sorted[count_/2])/2.0F; out=median*median; return std::isfinite(out);} private: float values_[kMaxSamples]{}; size_t count_{0}; };
