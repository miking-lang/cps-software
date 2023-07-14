#pragma once

#include <stdint.h>

#include "cps.h"

#define cps_rpc_send(x) CPS_RET_ON_ERR(cps_rpc_write(cps_rpc_client_fd, (x), sizeof(*(x))))
#define cps_rpc_send_dynarray(x, c) CPS_RET_ON_ERR(cps_rpc_write(cps_rpc_client_fd, (x), sizeof(*(x)) * (c)))
#define cps_rpc_recv(x) CPS_RET_ON_ERR(cps_rpc_read(cps_rpc_client_fd, (x), sizeof(*(x))))
#define cps_rpc_recv_dynarray(x, c) CPS_RET_ON_ERR(cps_rpc_read(cps_rpc_client_fd, (x), sizeof(*(x)) * (c)))

extern int cps_rpc_client_fd;
extern int cps_rpc_server_fd;

// forwad declaration of generated function id enum
typedef enum cps_rpc_cmd_t cps_rpc_cmd_t;

/** @brief Initialize RPC client.
 * 
 * @param ip connect host
 * @param port connect port
 * 
 * @retval CPS_ERR_SYS socket setup/connection failed
 * @retval CPS_ERR_OK no error
 */
cps_err_t cps_rpc_client_init(const char *ip, int port);


/** @brief Accept RPC client.
 * 
 * @retval CPS_ERR_SYS accept failed
 * @retval CPS_ERR_OK no error
 */
cps_err_t cps_rpc_server_accept(void);

/** @brief Initialize RPC server.
 * 
 * @param ip bind host
 * @param port bind port
 * 
 * @retval CPS_ERR_SYS socket setup failed
 * @retval CPS_ERR_OK no error
 */
cps_err_t cps_rpc_server_init(const char *ip, int port);

/** @brief Helper function. Read function id from the client socket.
 * 
 * @param fn function id
 * 
 * @retval CPS_ERR_RPC_SOCKET RPC socket read failed
 * @retval CPS_ERR_OK no error
 */
cps_err_t cps_rpc_read_fn(uint32_t *fn);

/** @brief Generated function. Handle specified server-side function.
 * 
 * @param fn function id
 * 
 * @retval CPS_ERR_RPC_SOCKET RPC socket read/write failed
 * @retval CPS_ERR_OK no error
 */
cps_err_t cps_rpc_handle(uint32_t fn);

/**
 * @brief Internal function. read() until count bytes have been read
 *
 * @param fd source file descriptor
 * @param buf target buffer
 * @param count number of bytes to write
 *
 * @retval CPS_ERR_RPC_SOCKET error in read() call
 * @retval CPS_ERR_OK no error
 */
cps_err_t cps_rpc_read(int fd, void *buf, size_t count);

/**
 * @brief Internal function. write() until count bytes have been written
 *
 * @param fd target file descriptor
 * @param buf source buffer
 * @param count number of bytes to write
 *
 * @retval CPS_ERR_RPC_SOCKET error in write() call
 * @retval CPS_ERR_OK no error
 */
cps_err_t cps_rpc_write(int fd, void *buf, size_t count);
