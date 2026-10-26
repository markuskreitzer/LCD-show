#pragma once

#include <stdint.h>
#include <limits.h>

inline bool ComputeFramebufferLayout(int width, int height, int left, int right,
                                    int top, int bottom, int &stride, int &bytes)
{
  if (width <= 0 || height <= 0 || left < 0 || right < 0 || top < 0 || bottom < 0)
    return false;
  const uint64_t fullWidth = static_cast<uint64_t>(width) + left + right;
  const uint64_t fullHeight = static_cast<uint64_t>(height) + top + bottom;
  if (fullWidth > static_cast<uint64_t>(INT_MAX - 31) / 2)
    return false;
  const uint64_t rowBytes = (fullWidth * 2 + 31) & ~static_cast<uint64_t>(31);
  if (fullHeight > static_cast<uint64_t>(INT_MAX / 2) / rowBytes)
    return false;
  stride = static_cast<int>(rowBytes);
  bytes = static_cast<int>(rowBytes * fullHeight);
  return true;
}
