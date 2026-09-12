#pragma once

#include <cstddef>

#include "CommandModel.h"

ParseCommandResult parseDeviceCommand(const char* payload, size_t length);
