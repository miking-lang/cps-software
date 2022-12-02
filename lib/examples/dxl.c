#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <unistd.h>

/* defining CPS_STRICT_ERR before including any CPS libraries will cause all
 * CPS_RET_ON_ERR to become CPS_ERR_CHECK
 * (see cps/cps.h for definitions of CPS_RET_ON_ERR and CPS_ERR_CHECK)
 *
 * this is good for debugging library code or to see where exactly in the
 * library function the error occured
 *
 * on the flip side, it will no longer be possible to see where in _your_
 * code the error occured (i.e. you can tell it happen inside a library
 * function, but not how your program got there)
 *
 * TL;DR: add this define to your code if you are having errors you don't
 * 		understand, it might just help
 */
// #define CPS_STRICT_ERR
#include "dxl.h"

/* see examples/accel.c for more detailed explanation of error checking */

int main(int argc, char *argv[]) {
	/* cps_err_t ret needs to be defined in functions that use CPS_ERR_CHECK
	 * or CPS_RET_ON_ERR.
	 */
	cps_err_t ret;
	int id, pos;

	if (argc != 2) {
		fprintf(stderr, "usage: %s <servo-id>\n", argv[0]);
		return 1;
	}
	id = atoi(argv[1]);

	/* initialize servo library with port "/dev/ttyUSB0", with error checking
	 */
	CPS_ERR_CHECK(dxl_init("/dev/ttyUSB0"));

	/* read current position of servo `id', with error checking */
	CPS_ERR_CHECK(dxl_get_current_position(id, &pos));
	printf("servo #%d is at %d (range 0-4096)\n", id, pos);

	pos = 1024;
	while (1) {
		printf("id: %d, pos: %d\n", id, pos);

		/* move servo `id' to absolute position `pos' (range 0-4096)
		 * in 1543 time units (milliseconds?), with error checking
		 */
		CPS_ERR_CHECK(dxl_servo_move_duration_abs(id, pos, 1543));
		sleep(2);

		/* swap target between 1k and 2k */
		pos = (pos == 2048) ? 1024 : 2048;
	}

	return 0;
}