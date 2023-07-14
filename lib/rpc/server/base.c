#include "cps.h"
#include "rpc.h"

#include <sys/socket.h> // socket, bind, listen, setsockopt
#include <arpa/inet.h> // inet_pton, sockaddr_in

int cps_rpc_server_fd;
int cps_rpc_client_fd;

cps_err_t cps_rpc_server_init(const char *ip, int port) {
    int opt = 1;
    struct sockaddr_in _addr;
    struct sockaddr *addr = (struct sockaddr *)&_addr;

    if ((cps_rpc_server_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        return CPS_ERR_SYS;
    }

    // reuse addr & port
    if (setsockopt(cps_rpc_server_fd, SOL_SOCKET,
                  SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt)) < 0) {
        return CPS_ERR_SYS;
    }

    _addr.sin_family = AF_INET;
    if (inet_pton(AF_INET, ip, &_addr.sin_addr) < 1) {
        return CPS_ERR_SYS;
    }
    _addr.sin_port = htons(port);

    if (bind(cps_rpc_server_fd, addr, sizeof(_addr)) < 0) {
        return CPS_ERR_SYS;
    }

    if (listen(cps_rpc_server_fd, 1) < 0) {
        return CPS_ERR_SYS;
    }

    return CPS_ERR_OK;
}

cps_err_t cps_rpc_server_accept(void) {
	socklen_t addrlen = 0;
    struct sockaddr_in _addr;
    struct sockaddr *addr = (struct sockaddr *)&_addr;

    if ((cps_rpc_client_fd = accept(cps_rpc_server_fd, addr, &addrlen)) < 0) {
        return CPS_ERR_SYS;
    }

    return CPS_ERR_OK;
}

cps_err_t cps_rpc_read_fn(uint32_t *fn) {
    cps_err_t ret;
    uint32_t tmp = 0;

    CPS_ERR_CHECK(cps_rpc_read(cps_rpc_client_fd, &tmp, sizeof(tmp)));
    *fn = tmp;

    return CPS_ERR_OK;
}
