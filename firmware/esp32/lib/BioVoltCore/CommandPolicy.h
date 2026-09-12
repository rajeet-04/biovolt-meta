#pragma once

#include "CommandModel.h"

enum class CommandPolicyDecision { Allowed, PhaseNotAvailable, SafetyRejected };

inline CommandPolicyDecision commandPolicy(const DeviceCommand& command, ControlMode currentMode) {
  switch (command.kind) {
    case CommandKind::SetMode:
      return command.requestedMode == ControlMode::Adaptive
                 ? CommandPolicyDecision::PhaseNotAvailable
                 : CommandPolicyDecision::Allowed;
    case CommandKind::SetLedPwm:
      return (currentMode == ControlMode::Passive || currentMode == ControlMode::Manual)
                 ? CommandPolicyDecision::Allowed
                 : CommandPolicyDecision::SafetyRejected;
    case CommandKind::SetMixer:
      return currentMode == ControlMode::Manual ? CommandPolicyDecision::Allowed
                                                 : CommandPolicyDecision::SafetyRejected;
    case CommandKind::RequestStatus:
    case CommandKind::SafeStop:
      return CommandPolicyDecision::Allowed;
  }
  return CommandPolicyDecision::SafetyRejected;
}
