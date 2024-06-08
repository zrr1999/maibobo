from __future__ import annotations

import binascii
from enum import Enum
from functools import reduce
from serial import Serial

from loguru import logger


class InstructionType(Enum):
    CONNECTION = [0x01, 0x01]
    START = [0x01, 0x02]
    STOP = [0x01, 0x03]

    CURRENT_PRESSURE_MESSAGE = [0x01, 0x05]
    PRESSURE_RESULTS_MESSAGE = [0x01, 0x06]
    ERROR_MESSAGE = [0x01, 0x07]


class MaiboboEngine:
    def __init__(self, port: str | None, *, timeout: int = 2):
        self.serial = Serial(
            port, baudrate=9600, bytesize=8, parity="N", stopbits=1, timeout=timeout
        )
        self.write_buff: list[int] = []
        self.read_buff: list[int] = []

    def write(self):
        cks = self.compute_cks()
        command = "".join(f"{x:02X}" for x in self.write_buff)
        logger.info(f"写入 cc80{command}{cks:02x}")
        self.serial.write(binascii.a2b_hex(f"cc80{command}{cks:02x}"))
        self.write_buff = []

    def read(self):
        read_data = self.serial.read(150 * 60).hex()
        if read_data == "":
            return None

        logger.info(f"读取 {read_data}")
        assert read_data.startswith("aa8003"), "数据读取出错"
        # 把字符串两两分组变成列表
        self.read_buff = [
            int(read_data[i : i + 2], 16) for i in range(4, len(read_data) - 2, 2)
        ]
        ins_type = self.read_buff[2:4]
        data = self.read_buff[4:]
        cks = read_data[-2:]
        assert self.compute_cks(False) == int(
            cks, 16
        ), f"校验码错误 {self.compute_cks(False):02x} != {cks}"
        if ins_type == InstructionType.ERROR_MESSAGE.value:
            mapping_code_msg = {
                0x01: "压力保护",
                0x02: "信号检测错误或上游气囊漏气，请重新测量",
                0x05: "信号检测错误或下游气囊漏气，请重新测量",
                0x06: "信号检测错误或传感器错误请重新测量",
                0x09: "放气异常",
                0x0F: "系统漏气",
                0x10: "电机错误",
            }
            data = data[0]
            if data in mapping_code_msg:
                raise RuntimeError(mapping_code_msg[data])
            else:
                raise RuntimeError(f"仪器出错(未知错误码{data})")
        elif ins_type == InstructionType.CURRENT_PRESSURE_MESSAGE.value:
            return data[0] * 256 + data[1]
        elif ins_type == InstructionType.PRESSURE_RESULTS_MESSAGE.value:
            # 收缩压，舒张压，脉搏
            logger.info(data)
            data = data[7:]
            return (
                data[0] * 256 + data[1],
                data[2] * 256 + data[3],
                data[4] * 256 + data[5],
            )
        else:
            logger.info(f"跳过不支持指令{self.read_buff}")

    def wait_read(self):
        read_data = self.serial.read(150 * 60).hex()
        for i in range(100):
            if read_data != "":
                break
            import time

            time.sleep(1)
            logger.info(f"第{i+1}次重试")
            read_data = self.serial.read(150 * 60).hex()
        logger.info(f"读取 {read_data}")
        assert read_data.startswith("aa8003"), "数据读取出错"
        # 把字符串两两分组变成列表
        self.read_buff = [
            int(read_data[i : i + 2], 16) for i in range(4, len(read_data) - 2, 2)
        ]
        cks = read_data[-2:]

        # length = self.read_buff[0]
        ins_type = self.read_buff[1:3]
        data = self.read_buff[3:]
        assert self.compute_cks(False) == int(
            cks, 16
        ), f"校验码错误 {self.compute_cks(False):02x} != {cks}"
        if ins_type == InstructionType.ERROR_MESSAGE.value:
            mapping_code_msg = {
                0x01: "压力保护",
                0x02: "信号检测错误或上游气囊漏气，请重新测量",
                0x05: "信号检测错误或下游气囊漏气，请重新测量",
                0x06: "信号检测错误或传感器错误请重新测量",
                0x09: "放气异常",
                0x0F: "系统漏气",
                0x10: "电机错误",
            }
            data = data[0]
            if data in mapping_code_msg:
                raise Exception(mapping_code_msg[data])
            else:
                raise Exception(f"仪器出错(未知错误码{data})")
        elif ins_type == InstructionType.CURRENT_PRESSURE_MESSAGE.value:
            return data[0] * 256 + data[1]
        elif ins_type == InstructionType.PRESSURE_RESULTS_MESSAGE.value:
            logger.info(data)
            # 收、舒、脉搏
            return (
                data[11] * 256 + data[12],
                data[13] * 256 + data[14],
                data[15] * 256 + data[16],
            )
        else:
            logger.info(f"跳过不支持指令{self.read_buff}")

    def compute_cks(self, write: bool = True):
        if write:
            return reduce(lambda x, y: x ^ y, self.write_buff)
        else:
            return reduce(lambda x, y: x ^ y, self.read_buff)

    def send(self, ins_type: InstructionType, data: list[int] | int = 0x00):
        if not isinstance(data, list):
            data = [data]
        self.write_buff.extend([0x03, len(data) + 2])
        self.write_buff.extend(ins_type.value)
        self.write_buff.extend(data)
        self.write()
        self.read()
        return self.read_buff

    def connect(self) -> bool:
        self.send(InstructionType.CONNECTION)
        return self.read_buff == "030301010000"

    def start(self) -> bool:
        self.send(InstructionType.START)
        return self.read_buff == "030301020000"

    def stop(self) -> bool:
        self.send(InstructionType.STOP)
        return self.read_buff == "030301030000"
