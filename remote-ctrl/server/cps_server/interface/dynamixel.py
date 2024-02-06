import dynamixel_sdk as dxl
from dynamixel_sdk import DXL_LOBYTE, DXL_LOWORD, DXL_HIBYTE, DXL_HIWORD

#https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/#control-table-data-address

import time

from typing import Union, List

class Register:
    def __init__(self, addr, bytelen, name):
        self.addr = addr
        self.bytelen = bytelen
        self.name = name
        self.ADDR = addr
        self.NAME = name

    def encode(self, value : int) -> List[int]:
        """Encodes a value as a list of bytes."""
        data = [
            DXL_LOBYTE(DXL_LOWORD(value)),
            DXL_HIBYTE(DXL_LOWORD(value)),
            DXL_LOBYTE(DXL_HIWORD(value)),
            DXL_HIBYTE(DXL_HIWORD(value)),
        ]
        return data[:self.bytelen]

    def decode_signed(self, value : int) -> int:
        """
        Decodes a signed integer value
        """
        ret = value
        if (1 << (self.bytelen*8-1)) & (value):
            # The value is a negative number in two's complement, we make sure
            # it's saved as negative also in Python
            ret = value - 2**(self.bytelen*8)
        return ret


REGISTER_LIST = [
    # Control Table of EEPROM Area
    Register(0,  bytelen=2, name="MODEL_NUMBER"),
    Register(2,  bytelen=4, name="MODEL_INFORMATION"),
    Register(6,  bytelen=1, name="FIRMWARE_VERSION"),
    Register(7,  bytelen=1, name="ID"),
    Register(8,  bytelen=1, name="BAUD_RATE"),
    Register(9,  bytelen=1, name="RETURN_DELAY_TIME"),
    Register(10, bytelen=1, name="DRIVE_MODE"),
    Register(11, bytelen=1, name="OPERATING_MODE"),
    Register(12, bytelen=1, name="SECONDARY_SHADOW_ID"),
    Register(13, bytelen=1, name="PROTOCOL_TYPE"),
    Register(20, bytelen=4, name="HOMING_OFFSET"),
    Register(24, bytelen=4, name="MOVING_THRESHOLD"),
    Register(31, bytelen=1, name="TEMPERATURE_LIMIT"),
    Register(32, bytelen=2, name="MAX_VOLTAGE_LIMIT"),
    Register(34, bytelen=2, name="MIN_VOLTAGE_LIMIT"),
    Register(36, bytelen=2, name="PWM_LIMIT"),
    Register(38, bytelen=2, name="CURRENT_LIMIT"),
    Register(44, bytelen=4, name="VELOCITY_LIMIT"),
    Register(48, bytelen=4, name="MAX_POSITION_LIMIT"),
    Register(52, bytelen=4, name="MIN_POSITION_LIMIT"),
    Register(60, bytelen=1, name="STARTUP_CONFIGURATION"),
    Register(63, bytelen=1, name="SHUTDOWN"),
    # Control Table of RAM Area
    Register(64,  bytelen=1, name="TORQUE_ENABLE"),
    Register(65,  bytelen=1, name="LED"),
    Register(68,  bytelen=1, name="STATUS_RETURN_LEVEL"),
    Register(69,  bytelen=1, name="REGISTERED_INSTRUCTION"),
    Register(70,  bytelen=1, name="HARDWARE_ERROR_STATUS"),
    Register(76,  bytelen=2, name="VELOCITY_I_GAIN"),
    Register(78,  bytelen=2, name="VELOCITY_P_GAIN"),
    Register(80,  bytelen=2, name="POSITION_D_GAIN"),
    Register(82,  bytelen=2, name="POSITION_I_GAIN"),
    Register(84,  bytelen=2, name="POSITION_P_GAIN"),
    Register(88,  bytelen=2, name="FEEDFORWARD_2ND_GAIN"),
    Register(90,  bytelen=2, name="FEEDFORWARD_1ST_GAIN"),
    Register(98,  bytelen=1, name="BUS_WATCHDOG"),
    Register(100, bytelen=2, name="GOAL_PWM"),
    Register(102, bytelen=2, name="GOAL_CURRENT"),
    Register(104, bytelen=4, name="GOAL_VELOCITY"),
    Register(108, bytelen=4, name="PROFILE_ACCELERATION"),
    Register(112, bytelen=4, name="PROFILE_VELOCITY"),
    Register(116, bytelen=4, name="GOAL_POSITION"),
    Register(120, bytelen=2, name="REALTIME_TICK"),
    Register(122, bytelen=1, name="MOVING"),
    Register(123, bytelen=1, name="MOVING_STATUS"),
    Register(124, bytelen=2, name="PRESENT_PWM"),
    Register(126, bytelen=2, name="PRESENT_CURRENT"),
    Register(128, bytelen=4, name="PRESENT_VELOCITY"),
    Register(132, bytelen=4, name="PRESENT_POSITION"),
    Register(136, bytelen=4, name="VELOCITY_TRAJECTORY"),
    Register(140, bytelen=4, name="POSITION_TRAJECTORY"),
    Register(144, bytelen=2, name="PRESENT_INPUT_VOLTAGE"),
    Register(146, bytelen=1, name="PRESENT_TEMPERATURE"),
    Register(147, bytelen=1, name="BACKUP_READY"),
]
# Add the 28 indirect address and data registers
INDIRECT_ADDRESS_REGISTERS = [
    Register(168 + i*2, bytelen=2, name=f"INDIRECT_ADDRESS_{i+1}")
    for i in range(28)
]
INDIRECT_DATA_REGISTERS = [
    Register(224 + i*1, bytelen=1, name=f"INDIRECT_DATA_{i+1}")
    for i in range(28)
]
REGISTER_LIST += INDIRECT_ADDRESS_REGISTERS
REGISTER_LIST += INDIRECT_DATA_REGISTERS

# Lookup for register
REGISTER_LOOKUP = {reg.name: reg for reg in REGISTER_LIST}

# With dot-notation as well (REGISTER.<name>)
REGISTER = type("REGISTER", (object,), REGISTER_LOOKUP)

POSITION_CONTROL_INDIRECTIONS = [
    REGISTER.TORQUE_ENABLE,
    REGISTER.PROFILE_VELOCITY,
    REGISTER.PROFILE_ACCELERATION,
    REGISTER.GOAL_POSITION,
]

# Previous definitions
#ADDR_DRIVE_MODE             = 10
#ADDR_TORQUE_ENABLE          = 64
#ADDR_GOAL_POSITION          = 116
#ADDR_PROFILE_VELOCITY       = 112
#ADDR_PRESENT_POSITION       = 132
#ADDR_POSITION_TRAJECTORY    = 140
#ADDR_VELOCITY_TRAJECTORY    = 136
#ADDR_PROFILE_ACCELERATION   = 108
#ADDR_PRESENT_VELOCITY       = 128
#ADDR_PRESENT_PWM            = 124
#ADDR_PRESENT_CURRENT        = 126
#BAUDRATE                    = 57600
#HIGH_BAUDRATE               = 1152000
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

    def setup_position_control(self, ids : List[int]):
        """
        Sets up the necessary registers

        From https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/#control-table-description

            CAUTION: Data in the EEPROM Area can only be written when the
                     value of Torque Enable(64) is cleared to ‘0’.
        """
        self.group_sync_write(REGISTER.TORQUE_ENABLE, ids, 0)
        self.group_sync_write(REGISTER.DRIVE_MODE,    ids, 4)
        addrs = []
        for reg in POSITION_CONTROL_INDIRECTIONS:
            for i in range(reg.bytelen):
                addrs.append(reg.addr + i)

        # Write all the target addresses
        for i, addr in enumerate(addrs):
            self.group_sync_write(INDIRECT_ADDRESS_REGISTERS[i], ids, addr)

    def position_control(self, ids : List[int], positions : List[int], duration : int, acceleration : int):
        """
        Performs position control in a single write.
        """
        writes = [
            (TORQUE_ENABLE,        1),
            (PROFILE_VELOCITY,     duration),
            (PROFILE_ACCELERATION, acceleration),
            (GOAL_POSITION,        positions),
        ]
        addr = REGISTER.INDIRECT_DATA_1.addr
        datalen = sum(reg.bytelen for (reg, _) in writes)

        groupSyncWrite = dxl.GroupSyncWrite(self.portHandler, self.packetHandler, addr, datalen)

        for i, id in enumerate(ids):
            data = []
            for reg, value in writes:
                if isinstance(value, list):
                    data += reg.encode(value[i])
                else:
                    data += reg.encode(value)

            groupSyncWrite.addParam(id, data)

        dxl_comm_result = groupSyncWrite.txPacket()
        if dxl_comm_result != dxl.COMM_SUCCESS:
            raise RuntimeError(f"{self.packetHandler.getTxRxResult(dxl_comm_result)}")

        groupSyncWrite.clearParam()


    def sync_read_all(self, ids : List[int]):
        """
        Reads all control RAM parameters from all servos.
        """
        reg_start = REGISTER.TORQUE_ENABLE
        reg_end = REGISTER.BACKUP_READY
        addr = reg_start.addr
        length = (reg_end.addr + reg_end.bytelen) - addr

        registers = [reg for reg in REGISTER_LIST if reg.addr >= reg_start.addr and reg.addr <= reg_end.addr]
        registers = sorted(registers, key=lambda r: r.addr)

        groupSyncRead = dxl.GroupSyncRead(self.portHandler, self.packetHandler, addr, length)

        for id in ids:
            groupSyncRead.addParam(id)

        dxl_comm_result = groupSyncRead.txRxPacket()
        if dxl_comm_result != dxl.COMM_SUCCESS:
            raise RuntimeError(f"Comm result: {self.packetHandler.getTxRxResult(dxl_comm_result)}")

        readregs = dict()

        reg_idx = 0
        end_addr = addr + end_addr

        while addr < end_addr and reg_idx < len(registers):
            reg = registers[reg_idx]
            if addr < reg.addr:
                addr = reg.addr

            readregs[reg.name] = []
            for id in ids:
                value = groupSyncRead.getData(id, reg.addr, reg.bytelen)
                readregs[reg.name].append(reg.decode_signed(value))

            addr += reg.bytelen

        return readregs


    def group_sync_write(self, reg : Register, ids : List[int], values : Union[List[int], int]):
        """
        Synchronized group write to all ids.
        """
        if isinstance(values, int):
            values = [values]*len(ids)

        groupSyncWrite = dxl.GroupSyncWrite(self.portHandler, self.packetHandler, reg.addr, reg.bytelen)
        for id, v in zip(ids, values):
            groupSyncWrite.addParam(id, reg.encode(v))

        dxl_comm_result = groupSyncWrite.txPacket()
        if dxl_comm_result != dxl.COMM_SUCCESS:
            raise RuntimeError(f"{self.packetHandler.getTxRxResult(dxl_comm_result)}")

        groupSyncWrite.clearParam()

    def group_sync_read(self, reg : Register, ids : List[int]):
        """
        Synchronized group read from all ids.
        """
        groupSyncRead = dxl.GroupSyncRead(self.portHandler, self.packetHandler, reg.addr, reg.bytelen)

        for id in ids:
            groupSyncRead.addParam(id)

        dxl_comm_result = groupSyncRead.txRxPacket()
        if dxl_comm_result != dxl.COMM_SUCCESS:
            raise RuntimeError(f"Comm result: {self.packetHandler.getTxRxResult(dxl_comm_result)}")

        res = []

        for id in ids:
            value = groupSyncRead.getData(id, reg.addr, reg.bytelen)
            #if (1 << (reg.bytelen*8-1)) & (value):
            #    # The value is a negative number in two's complement, we make sure it's saved as negative also in Python
            #    value = value - 2**(reg.bytelen*8)
            #res.append(value)
            res.append(reg.decode_signed(value))

        return res

    def move_many_servos(self, ids, positions, durations):
        self.group_sync_write(REGISTER.TORQUE_ENABLE,        ids, 1)
        self.group_sync_write(REGISTER.DRIVE_MODE,           ids, 4)
        self.group_sync_write(REGISTER.PROFILE_VELOCITY,     ids, durations)
        self.group_sync_write(REGISTER.PROFILE_ACCELERATION, ids, 600)
        self.group_sync_write(REGISTER.GOAL_POSITION,        ids, positions)

    def read_servo_positions(self, ids):
        return self.group_sync_read(REGISTER.PRESENT_POSITION, ids)

    def read_servo_position_trajectories(self, ids):
        return self.group_sync_read(REGISTER.POSITION_TRAJECTORY, ids)

    def read_servo_velocity_trajectories(self, ids):
        return self.group_sync_read(REGISTER.VELOCITY_TRAJECTORY, ids)

    def read_servo_velocities(self, ids):
        return self.group_sync_read(REGISTER.PRESENT_VELOCITY, ids)

    def read_servo_PWM(self, ids):
        return self.group_sync_read(REGISTER.PRESENT_PWM, ids)

    def read_servo_currents(self, ids):
        return self.group_sync_read(REGISTER.PRESENT_CURRENT, ids)

    def get_torque_enabled(self, ids):
        return self.group_sync_read(REGISTER.TORQUE_ENABLE, ids)

    def enable_torques(self, ids):
        return self.group_sync_write(REGISTER.TORQUE_ENABLE, ids, 1)

    def disable_torques(self, ids):
        return self.group_sync_write(REGISTER.TORQUE_ENABLE, ids, 0)
