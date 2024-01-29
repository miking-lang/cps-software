#!/usr/bin/env python
from dynamixel_sdk import *                    # Uses Dynamixel SDK library

ADDR_TORQUE_ENABLE          = 64
ADDR_GOAL_POSITION          = 116
ADDR_PROFILE_VELOCITY       = 112
ADDR_DRIVE_MODE             = 10
ADDR_PRESENT_POSITION       = 132
ADDR_PRESENT_VOLTAGE        = 144
ADDR_PROFILE_ACCELERATION   = 108
BAUDRATE                    = 57600
PROTOCOL_VERSION            = 2.0

class DynamixelHandler:
    def __init__(self):
        self.portHandler = PortHandler('/dev/tty.usbserial-FT6Z8AGE')

        self.packetHandler = PacketHandler(PROTOCOL_VERSION)
        if self.portHandler.openPort():
            print("Succeeded to open the port")
        else:
            print("Failed to open the port")
            quit()

        # Set port baudrate
        if self.portHandler.setBaudRate(BAUDRATE):
            print("Succeeded to change the baudrate")
        else:
            print("Failed to change the baudrate")
            quit()

    def move_many_servos(self, ids, positions, durations):
        groupSyncWrite = GroupSyncWrite(self.portHandler, self.packetHandler, ADDR_GOAL_POSITION, 4)

        for index, id in enumerate(ids):
            self.packetHandler.write1ByteTxRx(self.portHandler, id, ADDR_TORQUE_ENABLE, 1)
            self.packetHandler.write1ByteTxRx(self.portHandler, id, ADDR_DRIVE_MODE, 4)         # 4 = Time-based profile
            self.packetHandler.write4ByteTxRx(self.portHandler, id, ADDR_PROFILE_VELOCITY, durations[index])
            self.packetHandler.write4ByteTxRx(self.portHandler, id, ADDR_PROFILE_ACCELERATION, durations[index]//3)

            param_goal_position = [DXL_LOBYTE(DXL_LOWORD(positions[index])), DXL_HIBYTE(DXL_LOWORD(positions[index])), DXL_LOBYTE(DXL_HIWORD(positions[index])), DXL_HIBYTE(DXL_HIWORD(positions[index]))]
            groupSyncWrite.addParam(id, param_goal_position)

        dxl_comm_result = groupSyncWrite.txPacket()
        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % self.packetHandler.getTxRxResult(dxl_comm_result))

        groupSyncWrite.clearParam()

    def read_servos(self, ids, addr, bytelen):
        groupSyncRead = GroupSyncRead(self.portHandler, self.packetHandler, addr, int(bytelen))

        for id in ids:
            groupSyncRead.addParam(id)

        dxl_comm_result = groupSyncRead.txRxPacket()

        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % self.packetHandler.getTxRxResult(dxl_comm_result))

        res = []
        
        for id in ids:
            position = groupSyncRead.getData(id, addr, int(bytelen))
            res.append(position)

        return res

    def read_servo_positions(self, ids):
        return self.read_servos(ids, ADDR_PRESENT_POSITION, 4)

    def read_servo_voltages(self, ids):
        return self.read_servos(ids, ADDR_PRESENT_VOLTAGE, 2)

    def disable_torques(self, ids):
        for id in ids:
            self.packetHandler.write1ByteTxRx(self.portHandler, id, ADDR_TORQUE_ENABLE, 0)