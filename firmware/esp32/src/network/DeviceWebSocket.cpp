#include "DeviceWebSocket.h"

#include <Arduino.h>
#include <esp_timer.h>

#include "../../lib/BioVoltCore/AckSerializer.h"
#include "../../lib/BioVoltCore/CommandParser.h"
#include "Backoff.h"

DeviceWebSocket* DeviceWebSocket::active_ = nullptr;

void DeviceWebSocket::begin(const RuntimeConfig& config) {
  host_ = config.backendHost;
  path_ = config.backendPath;
  port_ = config.backendPort;
  deviceId_ = config.deviceId;
  headers_ = "X-BioVolt-Device-ID: " + config.deviceId + "\r\nAuthorization: Bearer " +
             config.deviceToken + "\r\n";
  active_ = this;
  client_.onEvent(DeviceWebSocket::eventCallback);
  state_ = WebSocketState::Disconnected;
  nextAttemptMs_ = 0;
  attempt_ = 0;
  if (!sendMutex_) sendMutex_ = xSemaphoreCreateMutex();
}

void DeviceWebSocket::startConnection(uint64_t nowMs) {
  client_.setExtraHeaders(headers_.c_str());
  client_.begin(host_.c_str(), port_, path_.c_str());
  state_ = WebSocketState::Connecting;
  nextAttemptMs_ = nowMs + reconnectDelayMs(attempt_);
  if (attempt_ < 4) ++attempt_;
}

void DeviceWebSocket::poll(uint64_t nowMs, bool networkConnected) {
  if (!networkConnected) {
    if (state_ != WebSocketState::Disconnected) client_.disconnect();
    state_ = WebSocketState::Disconnected;
    return;
  }
  client_.loop();
  if (state_ == WebSocketState::Disconnected && nowMs >= nextAttemptMs_) startConnection(nowMs);
}

bool DeviceWebSocket::sendText(const char* payload, size_t length) {
  if (!connected() || !payload || !sendMutex_ || xSemaphoreTake(sendMutex_, pdMS_TO_TICKS(100)) != pdTRUE) {
    return false;
  }
  const bool sent = client_.sendTXT(payload, length);
  xSemaphoreGive(sendMutex_);
  return sent;
}

bool DeviceWebSocket::sendAck(const DeviceAck& ack) {
  char payload[AckSerializer::kJsonCapacity];
  size_t written = 0;
  AckSerializer serializer;
  if (!serializer.serialize(ack, payload, sizeof(payload), written)) return false;
  return sendText(payload, written);
}

void DeviceWebSocket::eventCallback(WStype_t type, uint8_t* payload, size_t length) {
  if (active_) active_->handleEvent(type, payload, length);
}

void DeviceWebSocket::handleEvent(WStype_t type, uint8_t* payload, size_t length) {
  if (type == WStype_CONNECTED) {
    state_ = WebSocketState::Connected;
    attempt_ = 0;
    Serial.println("WebSocket connected");
  } else if (type == WStype_DISCONNECTED) {
    state_ = WebSocketState::Disconnected;
    nextAttemptMs_ = 0;
    Serial.println("WebSocket disconnected");
  } else if (type == WStype_TEXT && payload && length > 0 && commandQueue_) {
    const ParseCommandResult parsed = parseDeviceCommand(reinterpret_cast<const char*>(payload), length);
    if (!parsed.valid) {
      if (!parsed.command.commandId.empty()) {
        DeviceAck ack;
        ack.commandId = parsed.command.commandId;
        ack.deviceId = deviceId_;
        ack.status = AckStatus::Rejected;
        ack.uptimeMs = esp_timer_get_time() / 1000ULL;
        ack.reasonCode = parsed.reasonCode.empty() ? "invalid_payload" : parsed.reasonCode;
        ack.message = "command rejected by parser";
        sendAck(ack);
      }
      return;
    }
    if (parsed.command.deviceId != deviceId_) {
      DeviceAck ack;
      ack.commandId = parsed.command.commandId;
      ack.deviceId = deviceId_;
      ack.status = AckStatus::Rejected;
      ack.uptimeMs = esp_timer_get_time() / 1000ULL;
      ack.reasonCode = "invalid_payload";
      ack.message = "device id mismatch";
      sendAck(ack);
      return;
    }
    DeviceCommand command = parsed.command;
    command.receivedAtMs = esp_timer_get_time() / 1000ULL;
    CommandQueueItem item;
    if (!commandToQueueItem(command, item) ||
        xQueueSend(commandQueue_, &item, 0) != pdTRUE) {
      DeviceAck ack;
      ack.commandId = command.commandId;
      ack.deviceId = deviceId_;
      ack.status = AckStatus::Failed;
      ack.uptimeMs = command.receivedAtMs;
      ack.reasonCode = "internal_error";
      ack.message = "command queue full";
      sendAck(ack);
    }
  }
}
