/**
 * @file cps.h
 * @brief General CPS library.
 */
#pragma once
#include <stdlib.h>

/**
 * @brief Make sure `expr == CPS_ERR_OK`, otherwise log error and abort.
 * 
 * @param ret must be declared in function body
 * @param expr expression to check
 * @return `noreturn`
 */
#define CPS_ERR_CHECK(expr) if ((ret = (expr)) != CPS_ERR_OK) \
    { cps_print_error(ret, #expr, __FILE__, __LINE__); abort(); }

/**
 * @brief Force all errors to cause log-and-abort behaviour.
 * 
 * @details
 * Turn #CPS_RET_ON_ERR into #CPS_ERR_CHECK, effectively turning all library
 * errors fatal. This allows to debug errors inside library code, as the very
 * first instance of an error is reported right away.
 */
#ifndef CPS_STRICT_ERR
    #define CPS_STRICT_ERR 0
#endif

#if CPS_STRICT_ERR == 0
    /**
     * @brief Return from current function if `expr != CPS_ERR_OK`.
     * 
     * @param ret must be declared in function body
     * @param expr expression to check
     * 
     * @return `noreturn`
     */
    #define CPS_RET_ON_ERR(expr) if ((ret = (expr)) != CPS_ERR_OK) \
        { return ret; }
#else
    #define CPS_RET_ON_ERR CPS_ERR_CHECK
#endif

#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))

/** CPS common errors */
typedef enum {
    /** no error */
    CPS_ERR_OK = 0,
    /** generic error */
    CPS_ERR_FAIL,
    /** system error (check errno) */
    CPS_ERR_SYS,
    /** DXL error (see dxl_print_error) */
    CPS_ERR_DXL,
    /** bad argument */
    CPS_ERR_ARG,
    /** wrong drive mode on the DXL */
    CPS_ERR_DRIVE_MODE,
    /** torque off when trying to move DXL */
    CPS_ERR_TORQUE_OFF,
    /** torque on when trying to change drive mode on DXL */
    CPS_ERR_TORQUE_ON,
} cps_err_t;

/** Reverse mapping from error codes to strings */
extern const char *cps_err_t_str[];

/**
 * @brief Internal function. Print error information.
 * 
 * @param ret error code to debug
 * @param expr stringified expression
 * @param file source file
 * @param line source line
 */
void cps_print_error(cps_err_t ret, const char *expr, const char *file,
    int line);
