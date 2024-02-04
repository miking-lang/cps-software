FROM debian:bullseye-slim

ADD lib /opt/cps-software/lib
ADD remote-ctrl/server /opt/cps-software/remote-ctrl/server

SHELL ["/bin/bash", "-c"]

ENV LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"

RUN apt update \
 && apt install -y make cmake gcc g++ bash-completion libi2c-dev zip wget patch cython3 python3 python3-setuptools \
 && cp /opt/cps-software/remote-ctrl/server/bashrc.sh /root/.bashrc \
 && source /root/.bashrc \
 && cd /root \
 && wget https://github.com/ROBOTIS-GIT/DynamixelSDK/archive/3.7.31.zip \
 && unzip 3.7.31.zip \
 && patch -u DynamixelSDK-3.7.31/c/src/dynamixel_sdk/port_handler.c < /opt/cps-software/remote-ctrl/server/patches/fix-port_handler.c.patch \
 && patch -u DynamixelSDK-3.7.31/c/src/dynamixel_sdk/packet_handler.c < /opt/cps-software/remote-ctrl/server/patches/fix-packet_handler.c.patch \
 && patch -u DynamixelSDK-3.7.31/c/include/dynamixel_sdk/port_handler.h < /opt/cps-software/remote-ctrl/server/patches/fix-port_handler.h.patch \
 && patch -u DynamixelSDK-3.7.31/c/include/dynamixel_sdk/packet_handler.h < /opt/cps-software/remote-ctrl/server/patches/fix-packet_handler.h.patch \
 && make -C DynamixelSDK-3.7.31/c/build/linux_sbc install \
 && cd DynamixelSDK-3.7.31/python \
 && python3 setup.py install \
 && cd /root \
 && rm -rf DynamixelSDK-3.7.31 \
 && make -C /opt/cps-software/lib clean build-so install-so install-py \
 && echo "Done"

CMD ["/opt/cps-software/remote-ctrl/server/server_spider.py"]
