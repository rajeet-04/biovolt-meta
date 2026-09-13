# BioVolt actuator-safety drill

Record boot-safe PWM/mixer state, invalid PWM clamp/rejection, mixer maximum
runtime/cooldown, backend disconnect behavior, and Adaptive-to-Manual/Stop
preemption. Every command needs an ID and ACK/rejection outcome. Any unsafe
actuator output, stale replay, or optimizer write after preemption is a blocker.
