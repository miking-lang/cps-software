#include <unistd.h>

#include "rpc.h"

cps_err_t cps_rpc_read(int fd, void *buf, size_t count) {
    size_t nb = 0;
    while (nb < count) {
        int result = read(fd, buf + nb, count - nb);
        if (result < 1) {
            return CPS_ERR_RPC_SOCKET;
        }

        nb += result;
    }

    return CPS_ERR_OK;
}

cps_err_t cps_rpc_write(int fd, void *buf, size_t count) {
    size_t nb = 0;
    while (nb < count) {
        int result = write(fd, buf + nb, count - nb);
        if (result < 1) {
            return CPS_ERR_RPC_SOCKET;
        }

        nb += result;
    }

    return CPS_ERR_OK;
}
