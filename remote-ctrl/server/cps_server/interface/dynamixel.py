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

    def __repr__(self):
        return f"Register<{self.name}|addr={self.addr}|bytelen={self.bytelen}>"

    @property
    def blob(self):
        return {"name": self.name, "addr": self.addr, "bytelen": self.bytelen}

    @property
    def json(self):
        return self.blob

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
#BAUDRATE                    = 57600
#HIGH_BAUDRATE               = 1152000
#PROTOCOL_VERSION            = 2.0

#7   4.5M [bps]  0.000 [%]
#6   4M [bps]    0.000 [%]
#5   3M [bps]    0.000 [%]
#4   2M [bps]    0.000 [%]
#3   1M [bps]    0.000 [%]
#2   115,200 [bps]   0.000 [%]
#1(Default)  57,600 [bps]    0.000 [%]
#0   9,600 [bps]     0.000 [%]
VALID_BAUDRATES = [
    9600,
    57_600,
    115_200,
    1_000_000,
    2_000_000,
    3_000_000,
    4_000_000,
]

class DynamixelHandler:
    def __init__(self, dev="/dev/ttyUSB0", baudrate=57600, protocol_version=2.0):
        self.opened_port = False
        self.portHandler = dxl.PortHandler(dev)

        self.packetHandler = dxl.PacketHandler(protocol_version)
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

    def set_baud_rate(self, baudrate):
        """Sets the baud rate."""
        if not self.portHandler.setBaudRate(baudrate):
            raise RuntimeError(f"Failed to set baudrate to {baudrate}")

    def get_baud_rate(self):
        """Retrieves the current baud rate."""
        return self.portHandler.getBaudRate()

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

    def get_position_control_configured(self, ids : List[int]) -> List[bool]:
        """
        Returns true if the servo has the correct position control configured.
        """
        drive_modes = self.sync_read_registers(ids, REGISTER.DRIVE_MODE, REGISTER.DRIVE_MODE)["DRIVE_MODE"]

        addrs = []
        for reg in POSITION_CONTROL_INDIRECTIONS:
            for i in range(reg.bytelen):
                addrs.append(reg.addr + i)

        indirections = self.sync_read_registers(ids, INDIRECT_ADDRESS_REGISTERS[0], INDIRECT_ADDRESS_REGISTERS[len(addrs) - 1])

        result = []
        for i, id in enumerate(ids):
            ok = True
            ok &= drive_modes[i] == 4
            if drive_modes[i] != 4:
                ok = False
            for j, addr in enumerate(addrs):
                ok &= indirections[INDIRECT_ADDRESS_REGISTERS[j].name][i] == addr
            result.append(ok)

        return result

    def position_control(self, ids : List[int], positions : List[int], duration : Union[int, List[int]], acceleration : Union[int, List[int]]):
        """
        Performs position control in a single write.
        """
        writes = [
            (REGISTER.TORQUE_ENABLE,        1),
            (REGISTER.PROFILE_VELOCITY,     duration),
            (REGISTER.PROFILE_ACCELERATION, acceleration),
            (REGISTER.GOAL_POSITION,        positions),
        ]
        addr = REGISTER.INDIRECT_DATA_1.addr
        datalen = sum(reg.bytelen for (reg, _) in writes)

        groupSyncWrite = dxl.GroupSyncWrite(self.portHandler, self.packetHandler, addr, datalen)

        for i, id in enumerate(ids):
            data = []
            for reg, value in writes:
                if isinstance(value, (list, tuple)):
                    data += reg.encode(value[i])
                else:
                    data += reg.encode(value)

            groupSyncWrite.addParam(id, data)

        dxl_comm_result = groupSyncWrite.txPacket()
        if dxl_comm_result != dxl.COMM_SUCCESS:
            raise RuntimeError(f"{self.packetHandler.getTxRxResult(dxl_comm_result)}")

        groupSyncWrite.clearParam()


    def sync_read_registers(self,
                            ids : List[int],
                            reg_start : Union[Register, str],
                            reg_end : Union[Register, str]):
        """
        Reads all control RAM parameters from all servos.
        """
        if isinstance(reg_start, str):
            reg_start = REGISTER_LOOKUP[reg_start]
        if isinstance(reg_end, str):
            reg_end = REGISTER_LOOKUP[reg_end]
        addr = reg_start.addr
        length = (reg_end.addr + reg_end.bytelen) - addr
        assert length > 0, f"length = {length} ()"

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
        end_addr = addr + length

        while addr < end_addr and reg_idx < len(registers):
            reg = registers[reg_idx]
            if addr < reg.addr:
                addr = reg.addr

            readregs[reg.name] = []
            for id in ids:
                value = groupSyncRead.getData(id, reg.addr, reg.bytelen)
                readregs[reg.name].append(reg.decode_signed(value))

            addr += reg.bytelen
            reg_idx += 1

        return readregs

    def sync_read_all_RAM(self, ids : List[int]):
        return self.sync_read_registers(ids, reg_start=REGISTER.TORQUE_ENABLE, reg_end=REGISTER.BACKUP_READY)

    def sync_read_all_EEPROM(self, ids : List[int]):
        return self.sync_read_registers(ids, reg_start=REGISTER.MODEL_NUMBER, reg_end=REGISTER.SHUTDOWN)

    def group_sync_write(self,
                         reg : Union[Register, str],
                         ids : List[int],
                         values : Union[List[int], int]):
        """
        Synchronized group write to all ids.
        """
        if isinstance(reg, str):
            reg = REGISTER_LOOKUP[reg]
        if isinstance(values, int):
            values = [values]*len(ids)

        assert len(values) == len(ids), f"{len(values)} == {len(ids)}"

        groupSyncWrite = dxl.GroupSyncWrite(self.portHandler, self.packetHandler, reg.addr, reg.bytelen)
        for id, v in zip(ids, values):
            groupSyncWrite.addParam(id, reg.encode(v))

        dxl_comm_result = groupSyncWrite.txPacket()
        if dxl_comm_result != dxl.COMM_SUCCESS:
            raise RuntimeError(f"{self.packetHandler.getTxRxResult(dxl_comm_result)}")

        groupSyncWrite.clearParam()

    def get_torque_enabled(self, ids):
        return self.sync_read_registers(ids, REGISTER.TORQUE_ENABLE, REGISTER.TORQUE_ENABLE)

    def enable_torques(self, ids):
        return self.group_sync_write(REGISTER.TORQUE_ENABLE, ids, 1)

    def disable_torques(self, ids):
        return self.group_sync_write(REGISTER.TORQUE_ENABLE, ids, 0)

    def reboot_servos(self, ids):
        self.disable_torques(ids)
        for id in ids:
            dxl_comm_result, _ = self.packetHandler.reboot(self.portHandler, id)
            if dxl_comm_result != dxl.COMM_SUCCESS:
                raise RuntimeError(f"Error rebooting servos: {self.packetHandler.getTxRxResult(dxl_comm_result)}")
