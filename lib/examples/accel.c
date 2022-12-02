#include <stdio.h>
#include <unistd.h>

#include "accel.h"

int main(void) {
	/* cps_err_t ret needs to be defined in functions that use CPS_ERR_CHECK
	 * or CPS_RET_ON_ERR.
	 */
	cps_err_t ret;
	cps_accel_t acc;

	/* cps_accel_init(...) runs first, and if the return value
	 * is not CPS_ERR_OK, CPS_ERR_CHECK will call cps_print_error(...),
	 * which will print out error information (name, file, line and expression)
	 */
	CPS_ERR_CHECK(cps_accel_init(&acc, "/dev/i2c-1", 0x68, ACC_SCALE_2_G,
		GYRO_SCALE_2000_DEG));

	for (;;) {
		float result;

		/* read acceleration in the X direction and do error checking
		 *
		 * if a function that returns cps_err_t (basically all of them) has
		 * to return a value (e.g. cps_accel_read_accel has to return
		 * acceleration), it will be done through a pointer, which is
		 * the last argument
		 *
		 * i.e. `result' will store the return value
		 */
		CPS_ERR_CHECK(cps_accel_read_accel(&acc, ACC_DIR_X, &result));
		printf("x: % 2.3f", result);

		/* same, this time for y */
		CPS_ERR_CHECK(cps_accel_read_accel(&acc, ACC_DIR_Y, &result));
		printf(" | y: % 2.3f", result);

		/* and for z */
		CPS_ERR_CHECK(cps_accel_read_accel(&acc, ACC_DIR_Z, &result));
		printf(" | z: % 2.3f\n", result);
		usleep(1000 * 500);
	}

	return 0;
}