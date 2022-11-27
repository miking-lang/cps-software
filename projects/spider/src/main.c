#include "dxl.h"

int main(void) {
	DXL_ERROR_CHECK(dxl_init("/dev/ttyUSB0"));
	return 0;
}