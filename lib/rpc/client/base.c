#include "cps.h"

#include <sys/socket.h> // socket, connect
#include <arpa/inet.h> // inet_pton, sockaddr_in

int cps_rpc_client_fd;

cps_err_t cps_rpc_client_init(const char *ip, int port) {
	struct sockaddr_in _addr;
	struct sockaddr *addr = (struct sockaddr *)&_addr;

	if ((cps_rpc_client_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
		return CPS_ERR_SYS;
	}

	_addr.sin_family = AF_INET;
	_addr.sin_port = htons(port);
	if (inet_pton(AF_INET, ip, &_addr.sin_addr) < 1) {
		return CPS_ERR_SYS;
	}

	if (connect(cps_rpc_client_fd, addr, sizeof(_addr)) < 0) {
		return CPS_ERR_SYS;
	}

	return CPS_ERR_OK;
}
