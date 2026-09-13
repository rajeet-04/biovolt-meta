#include "CommandTask.h"

#include <Arduino.h>
#include <esp_timer.h>

#include "../../lib/BioVoltCore/CommandPolicy.h"

namespace {
DeviceAck baseAck(const DeviceCommand& command, uint64_t nowMs) {
  DeviceAck ack;
  ack.commandId = command.commandId;
  ack.deviceId = command.deviceId;
  ack.uptimeMs = nowMs;
  return ack;
}

DeviceAck reject(const DeviceCommand& command, uint64_t nowMs, const char* reason,
                 const char* message) {
  DeviceAck ack = baseAck(command, nowMs);
  ack.status = AckStatus::Rejected;
  ack.reasonCode = reason;
  ack.message = message;
  return ack;
}

DeviceAck applyCommand(const DeviceCommand& command, uint64_t nowMs,
                       CommandTaskContext& context) {
  RuntimeSnapshot snapshot = context.state->snapshot();
  const CommandPolicyDecision decision = commandPolicy(command, snapshot.control.mode);
  if (decision == CommandPolicyDecision::PhaseNotAvailable) {
    return reject(command, nowMs, "phase_not_available", "adaptive mode is unavailable");
  }
  if (decision == CommandPolicyDecision::SafetyRejected) {
    return reject(command, nowMs, "safety_rejected", "command is not allowed in this mode");
  }

  ControlState control = snapshot.control;
  ActuatorState actuators = snapshot.actuators;
  if (command.kind == CommandKind::SetMode) {
    control.mode = command.requestedMode;
    context.state->updateControl(control);
    if (control.mode == ControlMode::Monitor) {
      ActuatorRequest request;
      request.growLedPwm = 0;
      request.mixerOn = false;
      actuators = context.controller->apply(request, nowMs);
      context.state->updateActuators(actuators);
    }
  } else if (command.kind == CommandKind::SetLedPwm) {
    ActuatorRequest request;
    request.growLedPwm = static_cast<int>(command.requestedPwm);
    request.mixerOn = actuators.mixerOn;
    actuators = context.controller->apply(request, nowMs);
    context.state->updateActuators(actuators);
  } else if (command.kind == CommandKind::SetMixer) {
    ActuatorRequest request;
    request.growLedPwm = static_cast<int>(actuators.growLedPwm);
    request.mixerOn = command.requestedMixerOn;
    actuators = context.controller->apply(request, nowMs);
    context.state->updateActuators(actuators);
    if (actuators.mixerOn != command.requestedMixerOn) {
      return reject(command, nowMs, "cooldown_active", "mixer safety policy rejected request");
    }
  } else if (command.kind == CommandKind::SafeStop) {
    control.mode = ControlMode::Monitor;
    control.optimizerDirection = 0;
    context.state->updateControl(control);
    ActuatorRequest request;
    request.growLedPwm = 0;
    request.mixerOn = false;
    actuators = context.controller->apply(request, nowMs);
    context.state->updateActuators(actuators);
  }

  snapshot = context.state->snapshot();
  DeviceAck ack = baseAck(command, nowMs);
  ack.status = AckStatus::Applied;
  ack.appliedMode = snapshot.control.mode;
  ack.appliedState = snapshot.actuators;
  ack.includeAppliedState = true;
  return ack;
}
}  // namespace

void commandTaskEntry(void* rawContext) {
  auto* context = static_cast<CommandTaskContext*>(rawContext);
  CommandDedupe dedupe;
  CommandQueueItem item;
  for (;;) {
    if (!context || !context->commandQueue || !context->state || !context->controller ||
        !context->websocket) {
      vTaskDelay(pdMS_TO_TICKS(100));
      continue;
    }
    if (xQueueReceive(context->commandQueue, &item, pdMS_TO_TICKS(100)) != pdTRUE) continue;
    const DeviceCommand command = commandFromQueueItem(item);
    DeviceAck ack;
    if (dedupe.find(command.commandId, ack)) {
      context->websocket->sendAck(ack);
      continue;
    }
    const uint64_t nowMs = esp_timer_get_time() / 1000ULL;
    if (nowMs - command.receivedAtMs >= command.ttlMs) {
      ack = reject(command, nowMs, "expired", "command TTL expired before application");
    } else {
      ack = applyCommand(command, nowMs, *context);
    }
    dedupe.remember(command.commandId, ack);
    context->websocket->sendAck(ack);
  }
}
