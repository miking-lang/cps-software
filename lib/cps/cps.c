#include <stdio.h>

#include "cps.h"

const char *cps_err_t_str[] = {
    [CPS_ERR_OK]         = "CPS_ERR_OK",
    [CPS_ERR_FAIL]       = "CPS_ERR_FAIL",
    [CPS_ERR_SYS]        = "CPS_ERR_SYS",
    [CPS_ERR_DXL]        = "CPS_ERR_DXL",
    [CPS_ERR_ARG]        = "CPS_ERR_ARG",
    [CPS_ERR_DRIVE_MODE] = "CPS_ERR_DRIVE_MODE",
    [CPS_ERR_TORQUE_OFF] = "CPS_ERR_TORQUE_OFF",
    [CPS_ERR_TORQUE_ON]  = "CPS_ERR_TORQUE_ON",
};

__attribute__((weak)) void dxl_print_error(void) {}

void cps_print_error(cps_err_t ret, const char *expr, const char *file,
        int line) {
    fprintf(stderr, "%s:%d: %s in (%s)\n", file, line, expr,
        cps_err_t_str[ret]);

    switch (ret) {
    case CPS_ERR_SYS:
        perror(NULL);
        break;
    case CPS_ERR_DXL:
        dxl_print_error();
        break;
    default:
        break;
    }
}
