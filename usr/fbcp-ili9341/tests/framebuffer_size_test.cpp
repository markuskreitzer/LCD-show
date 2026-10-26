#include "../framebuffer_size.h"

int main()
{
  int stride = 0, bytes = 0;
  if (!ComputeFramebufferLayout(640, 480, 0, 0, 0, 0, stride, bytes) || stride != 1280 || bytes != 614400)
    return 1;
  if (!ComputeFramebufferLayout(320, 240, 16, 16, 8, 8, stride, bytes) || stride != 704 || bytes != 180224)
    return 2;
  if (ComputeFramebufferLayout(0, 480, 0, 0, 0, 0, stride, bytes) ||
      ComputeFramebufferLayout(-1, 480, 0, 0, 0, 0, stride, bytes) ||
      ComputeFramebufferLayout(640, 480, -1, 0, 0, 0, stride, bytes))
    return 3;
  if (ComputeFramebufferLayout(INT_MAX, 1, 0, 0, 0, 0, stride, bytes) ||
      ComputeFramebufferLayout(640, 480, INT_MAX, INT_MAX, 0, 0, stride, bytes) ||
      ComputeFramebufferLayout(32768, 65536, 0, 0, 0, 0, stride, bytes))
    return 4;
  if (!ComputeFramebufferLayout(16, INT_MAX / 64, 0, 0, 0, 0, stride, bytes))
    return 5;
  if (ComputeFramebufferLayout(16, INT_MAX / 64 + 1, 0, 0, 0, 0, stride, bytes))
    return 6;
  return 0;
}
