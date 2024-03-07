FROM debian:bookworm-slim

ADD lib /opt/cps-software/lib
ADD remote-ctrl/server /opt/cps-software/remote-ctrl/server

SHELL ["/bin/bash", "-c"]

ENV LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"

RUN apt-get update \
 && apt-get install -y make cmake gcc g++ bash-completion libi2c-dev zip wget patch python3-full python3-dev \
 && python3 -m venv /root/py-venv \
 && cp /opt/cps-software/remote-ctrl/server/bashrc.sh /root/.bashrc \
 && source /root/.bashrc \
 && pip3 install torch --index-url https://download.pytorch.org/whl/cpu \
 && pip3 install Cython tqdm tensorboard "stable-baselines3 >= 2.2.1" "gymnasium==0.28.1" \
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
 && echo "Removing build packages" \
 && apt-get remove -y make cmake gcc g++ patch \
 && apt-get autoremove -y \
 && apt-get clean -y \
 && pip3 cache purge \
 && echo "Done"

CMD ["/bin/bash"]
