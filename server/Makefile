.PHONY: test-docker


# Test rule for messing around with docker...
# Bind the repo to /mnt as read-only
test-docker:
	$(eval PWD := $(shell pwd -P))
	$(eval DOCKERNAME := cps-software-test)
	$(eval RUNCMD := $(shell echo \
		"apt update; " \
		"apt install -y make cmake gcc g++ bash-completion libi2c-dev zip wget patch; " \
		"cp /mnt/server/bashrc.sh /root/.bashrc; " \
		"source /root/.bashrc; " \
		"cd /root; " \
		"wget https://github.com/ROBOTIS-GIT/DynamixelSDK/archive/3.7.31.zip && " \
		"unzip 3.7.31.zip && " \
		"patch -u DynamixelSDK-3.7.31/c/src/dynamixel_sdk/port_handler.c < /mnt/server/patches/fix-port_handler.c.patch && " \
		"patch -u DynamixelSDK-3.7.31/c/src/dynamixel_sdk/packet_handler.c < /mnt/server/patches/fix-packet_handler.c.patch && " \
		"patch -u DynamixelSDK-3.7.31/c/include/dynamixel_sdk/port_handler.h < /mnt/server/patches/fix-port_handler.h.patch && " \
		"patch -u DynamixelSDK-3.7.31/c/include/dynamixel_sdk/packet_handler.h < /mnt/server/patches/fix-packet_handler.h.patch && " \
		"make -C DynamixelSDK-3.7.31/c/build/linux_sbc install; " \
		"bash"))
	docker run --rm -it \
	       --hostname "$(DOCKERNAME)" \
	       --name "$(DOCKERNAME)" \
	       --volume "$(PWD)/..:/mnt:ro" \
	       --privileged \
	       debian:bullseye-slim \
	       bash -c '$(RUNCMD)'
