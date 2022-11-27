#include "dxl.h"
#include "accel.h"

int main(void) {
	DXL_ERROR_CHECK(dxl_init("/dev/ttyUSB0"));
	cps_accel_read_accel(NULL, 0, 0, NULL);
	return 0;
}