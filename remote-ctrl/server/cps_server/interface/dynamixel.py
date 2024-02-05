import dynamixel_sdk as dxl
from dynamixel_sdk import DXL_LOBYTE, DXL_LOWORD, DXL_HIBYTE, DXL_HIWORD

#https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/#control-table-data-address

import time

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
    def __init__(self, dev="/dev/ttyUSB0", baudrate=57600):
        self.opened_port = False
        self.portHandler = dxl.PortHandler(dev)

        self.packetHandler = dxl.PacketHandler(PROTOCOL_VERSION)
        if not self.portHandler.openPort():
            raise RuntimeError("Failed to open the port")

        self.opened_port = True

        # Set port baudrate
        if not self.portHandler.setBaudRate(baudrate):
            self.close()
            raise RuntimeError(f"Failed to set baudrate to {baudrate}")

    def __del__(self):
        self.close()

    def close(self):
        if self.opened_port:
            print("Closing port", flush=True)
            self.portHandler.closePort()

    def group_write_all_servos(self, ids, addr, values, bytelen=4):
        """Group write to all servos."""
        if bytelen not in [1,2,4]:
            raise ValueError("Expected bytelen to be either 1, 2, or 4.")

        groupSyncWrite = dxl.GroupSyncWrite(self.portHandler, self.packetHandler, addr, bytelen)
        for id, v in zip(ids, values):
            data = [
                DXL_LOBYTE(DXL_LOWORD(v)),
                DXL_HIBYTE(DXL_LOWORD(v)),
                DXL_LOBYTE(DXL_HIWORD(v)),
                DXL_HIBYTE(DXL_HIWORD(v))
            ]
            groupSyncWrite.addParam(id, data[:bytelen])

        dxl_comm_result = groupSyncWrite.txPacket()
        if dxl_comm_result != dxl.COMM_SUCCESS:
            raise RuntimeError(f"{self.packetHandler.getTxRxResult(dxl_comm_result)}")

        groupSyncWrite.clearParam()

    def move_many_servos(self, ids, positions, durations):
        self.group_write_all_servos(ids, [1]*len(ids), ADDR_TORQUE_ENABLE, bytelen=1)
        self.group_write_all_servos(ids, [4]*len(ids), ADDR_DRIVE_MODE, bytelen=1)
        self.group_write_all_servos(ids, durations, ADDR_PROFILE_VELOCITY, bytelen=4)
        self.group_write_all_servos(ids, [600]*len(ids), ADDR_PROFILE_ACCELERATION, bytelen=4)
        self.group_write_all_servos(ids, positions, ADDR_PROFILE_ACCELERATION, bytelen=4)
        return None # ignore below

        groupSyncWrite = dxl.GroupSyncWrite(self.portHandler, self.packetHandler, ADDR_GOAL_POSITION, 4)

        for index, id in enumerate(ids):
            self.packetHandler.write1ByteTxRx(self.portHandler, id, ADDR_TORQUE_ENABLE, 1)
            self.packetHandler.write1ByteTxRx(self.portHandler, id, ADDR_DRIVE_MODE, 4)         # 4 = Time-based profile
            self.packetHandler.write4ByteTxRx(self.portHandler, id, ADDR_PROFILE_VELOCITY, durations[index])
            self.packetHandler.write4ByteTxRx(self.portHandler, id, ADDR_PROFILE_ACCELERATION, 600)         #0.6s acceleration duration

            param_goal_position = [
                DXL_LOBYTE(DXL_LOWORD(positions[index])),
                DXL_HIBYTE(DXL_LOWORD(positions[index])),
                DXL_LOBYTE(DXL_HIWORD(positions[index])),
                DXL_HIBYTE(DXL_HIWORD(positions[index]))
            ]
            groupSyncWrite.addParam(id, param_goal_position)

        dxl_comm_result = groupSyncWrite.txPacket()
        if dxl_comm_result != dxl.COMM_SUCCESS:
            raise RuntimeError(f"{self.packetHandler.getTxRxResult(dxl_comm_result)}")

        groupSyncWrite.clearParam()

    def read_servo(self, ids, address, bytelen=4):
        groupSyncRead = dxl.GroupSyncRead(self.portHandler, self.packetHandler, address, bytelen)

        for id in ids:
            groupSyncRead.addParam(id)

        start_time = time.time()
        dxl_comm_result = groupSyncRead.txRxPacket()
        end_time = time.time()
        if dxl_comm_result != dxl.COMM_SUCCESS:
            raise RuntimeError(f"{self.packetHandler.getTxRxResult(dxl_comm_result)}")

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

    def enable_torques(self, ids):
        for id in ids:
            self.packetHandler.write1ByteTxRx(self.portHandler, id, ADDR_TORQUE_ENABLE, 1)

    def disable_torques(self, ids):
        for id in ids:
            self.packetHandler.write1ByteTxRx(self.portHandler, id, ADDR_TORQUE_ENABLE, 0)

    def get_torque_enabled(self, ids):
        return self.read_servo(ids, ADDR_TORQUE_ENABLE, 1)
