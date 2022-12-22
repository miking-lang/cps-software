#pragma once
#include <stdlib.h>

#define CPS_ERR_CHECK(expr) if ((ret = (expr)) != CPS_ERR_OK) \
    { cps_print_error(ret, #expr, __FILE__, __LINE__); abort(); }

#ifdef CPS_STRICT_ERR
    #define CPS_RET_ON_ERR CPS_ERR_CHECK
#else
    #define CPS_RET_ON_ERR(stmt) if ((ret = (stmt)) != CPS_ERR_OK) \
        { return ret; }
#endif

#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))

typedef enum {
    CPS_ERR_OK = 0,
    CPS_ERR_FAIL,   /* generic error */
    CPS_ERR_SYS,    /* system error (check errno) */
    CPS_ERR_DXL,	/* DXL error (see dxl_print_error) */
    CPS_ERR_ARG,    /* bad argument */
    CPS_ERR_DRIVE_MODE, /* wrong drive mode on the DXL */
    CPS_ERR_TORQUE_OFF, /* torque off when trying to move DXL */
    CPS_ERR_TORQUE_ON, /* torque on when trying to change drive mode on DXL */
} cps_err_t;

extern const char *cps_err_t_str[];

void cps_print_error(cps_err_t ret, const char *expr, const char *file,
    int line);
