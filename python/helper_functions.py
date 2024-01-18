#!/usr/bin/env python
from dynamixel_sdk import *                    # Uses Dynamixel SDK library

ADDR_TORQUE_ENABLE          = 64
ADDR_GOAL_POSITION          = 116
ADDR_PROFILE_VELOCITY       = 112
ADDR_DRIVE_MODE             = 10
ADDR_PRESENT_POSITION       = 132
ADDR_POSITION_TRAJECTORY    = 140
ADDR_VELOCITY_TRAJECTORY    = 136
ADDR_PROFILE_ACCELERATION   = 108
ADDR_PRESENT_VELOCITY       = 128
ADDR_PRESENT_PWM            = 124
ADDR_PRESENT_CURRENT        = 126
BAUDRATE                    = 57600
PROTOCOL_VERSION            = 2.0

class DynamixelHandler:
    def __init__(self):
        self.portHandler = PortHandler('/dev/ttyUSB0')

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
            self.packetHandler.write4ByteTxRx(self.portHandler, id, ADDR_PROFILE_ACCELERATION, 600)         #0.6s acceleration duration

            param_goal_position = [DXL_LOBYTE(DXL_LOWORD(positions[index])), DXL_HIBYTE(DXL_LOWORD(positions[index])), DXL_LOBYTE(DXL_HIWORD(positions[index])), DXL_HIBYTE(DXL_HIWORD(positions[index]))]
            groupSyncWrite.addParam(id, param_goal_position)

        dxl_comm_result = groupSyncWrite.txPacket()
        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % self.packetHandler.getTxRxResult(dxl_comm_result))

        groupSyncWrite.clearParam()

    def read_servo(self, ids, address, bytelen=4):
        groupSyncRead = GroupSyncRead(self.portHandler, self.packetHandler, address, bytelen)

        for id in ids:
            groupSyncRead.addParam(id)

        start_time = time.time()
        dxl_comm_result = groupSyncRead.txRxPacket()
        end_time = time.time()
        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % self.packetHandler.getTxRxResult(dxl_comm_result))
            
        res = []
        
        for id in ids:
            position = groupSyncRead.getData(id, address, bytelen)
            if (1 << (bytelen*8-1)) & (position):  # The position is a negative number in two's complement, we make sure it's saved as negative also in Python
                new_position = position - 2**(bytelen*8)
                position = new_position
            res.append(position)

        return res

    def read_servo_positions(self, ids):
        return self.read_servo(ids, ADDR_PRESENT_POSITION)

    def read_servo_position_trajectories(self, ids):
        return self.read_servo(ids, ADDR_POSITION_TRAJECTORY)

    def read_servo_velocity_trajectories(self, ids):
        return self.read_servo(ids, ADDR_VELOCITY_TRAJECTORY)

    def read_servo_velocities(self, ids):
        return self.read_servo(ids, ADDR_PRESENT_VELOCITY)

    def read_servo_PWM(self, ids):
        return self.read_servo(ids, ADDR_PRESENT_PWM, 2)

    def read_servo_currents(self, ids):
        return self.read_servo(ids, ADDR_PRESENT_CURRENT, 2)

    def disable_torques(self, ids):
        for id in ids:
            self.packetHandler.write1ByteTxRx(self.portHandler, id, ADDR_TORQUE_ENABLE, 0)