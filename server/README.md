# Server For Remote Control of the Spider

Download dynamixel SDK, patch their SRC files to not define variables in
headers, then build it.

Culprits:
 - port_handler.h: g_is_using, g_used_port_num
 - packet_handler.h: packetData

Make these external, then move definition to C files port_handler.c and packet_handler.c repectively.

```c
int     g_used_port_num; -> extern int     g_used_port_num;

uint8_t    *g_is_using;  -> extern uint8_t    *g_is_using;

PacketData *packetData; ->  extern PacketData *packetData;
```

```sh
wget https://github.com/ROBOTIS-GIT/DynamixelSDK/archive/3.7.31.zip
unzip 3.7.31.zip
patch -u DynamixelSDK-3.7.31/c/src/dynamixel_sdk/port_handler.c < /mnt/server/patches/fix-port_handler.c.patch
patch -u DynamixelSDK-3.7.31/c/src/dynamixel_sdk/packet_handler.c < /mnt/server/patches/fix-packet_handler.c.patch
patch -u DynamixelSDK-3.7.31/c/include/dynamixel_sdk/port_handler.h < /mnt/server/patches/fix-port_handler.h.patch
patch -u DynamixelSDK-3.7.31/c/include/dynamixel_sdk/packet_handler.h < /mnt/server/patches/fix-packet_handler.h.patch
make -C c/build/linux_sbc install

```
