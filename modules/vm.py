import sys
import typing as t
from random import randint

from .getch import getch


class InputWrapper:
    @staticmethod
    def read(_):
        return getch()


class VirtualMachine:
    def __init__(self, mem_size: int = 14, out_buffer_size: int = 8, output: t.Any = sys.stdout, input_: t.Any = InputWrapper):
        self.__PRECALC = {
            "COMS": "L^'GB+-*/%N?=W!PRA><#FI&|",  # "\0^'GB+-*/%N?=L~W!PRA><#FI|"
            "MEM_SIZE": 1 << mem_size,
            "MEM_MASK": (1 << mem_size) - 1,
            "OUT_SIZE": 1 << out_buffer_size,
            "OUT_MASK": (1 << out_buffer_size) - 1
        }
        self.__stdout = output
        self.__stdin = input_

        self.__memory: bytearray = bytearray([0] * self.__PRECALC["MEM_SIZE"])
        self.__address: int = 0

        self.__output: bytearray = bytearray([0] * self.__PRECALC["OUT_SIZE"])
        self.__carriage: int = 0

        self.__buffer: int = 0

    @property
    def memory(self):
        return bytes(self.__memory)

    @property
    def address(self):
        return self.__address

    @property
    def output(self):
        return bytes(self.__output)

    @property
    def carriage(self):
        return self.__carriage

    @property
    def buffer(self):
        return self.__buffer

    def _get_arg(self, arg):
        """Returns value of current memory cell if arg = 16"""
        if arg == 16:
            return self.__memory[self.__address]
        return arg

    def _add_to_output(self, ch):
        self.__output[self.__carriage] = ch & 0b01111111
        self.__carriage += 1
        self.__carriage &= self.__PRECALC["OUT_MASK"]

    def execute_command(self, com: int, arg: int):
        cch = self.__PRECALC["COMS"][com]
        arg = arg & 255
        if cch == '^':
            self.__buffer = arg
        elif cch == "'":
            self._add_to_output(arg)
        elif cch == '+':
            self.__buffer += self._get_arg(arg)
            self.__buffer &= 255
        elif cch == '-':
            self.__buffer -= self._get_arg(arg)
            self.__buffer &= 255
        elif cch == '*':
            self.__buffer *= self._get_arg(arg)
            self.__buffer &= 255
        elif cch == '/':
            self.__buffer //= self._get_arg(arg)
            self.__buffer &= 255
        elif cch == '%':
            self.__buffer %= self._get_arg(arg)
            self.__buffer &= 255
        elif cch == 'N':
            self.__buffer = randint(0, self._get_arg(arg))
        elif cch == '?':
            self.__buffer = int(self.__buffer > self._get_arg(arg)) * 0xFF
        elif cch == '=':
            self.__buffer = int(self.__buffer == self._get_arg(arg)) * 0xFF
        elif cch == 'W':
            self.__memory[self.__address] = self.__buffer
        elif cch == '!':
            self.__buffer = 0xFF - self.__buffer
        elif cch == 'P':
            self.__buffer = self.__address & 255
        elif cch == 'R':
            self.__buffer = self.__memory[self.__address]
        elif cch == 'A':
            self.__address = (self.__address >> 8 << 8) + self.__buffer
            self.__address &= self.__PRECALC["MEM_MASK"]
        elif cch == '>':
            self.__address += 1
            self.__address &= self.__PRECALC["MEM_MASK"]
        elif cch == '<':
            self.__address -= 1
            self.__address &= self.__PRECALC["MEM_MASK"]
        elif cch == '#':
            self._add_to_output(self.__buffer)
        elif cch == 'F':
            self.__stdout.write(self.__output[:self.__carriage].decode(encoding='ascii'))
            self.__stdout.flush()
            self.__carriage = 0
        elif cch == 'I':
            self.__buffer = ord(self.__stdin.read(1)) & 255
        elif cch == '&':
            self.__buffer &= self._get_arg(arg)
        elif cch == '|':
            self.__buffer |= self._get_arg(arg)

    def execute(self, program: bytes):
        for _ in self.execute_by_step(program):
            pass

    def execute_by_step(self, program: bytes):
        i = 0
        while i < len(program):
            com, arg = program[i:i+2]
            cch = self.__PRECALC["COMS"][com]

            if cch == 'G' and self.__buffer:
                arg = self._get_arg(arg)
                while arg > 0:
                    i += 2
                    if self.__PRECALC["COMS"][program[i]] == 'L':  # L
                        arg -= 1

            elif cch == 'B' and self.__buffer:
                arg = self._get_arg(arg)
                while arg > 0:
                    i -= 2
                    if self.__PRECALC["COMS"][program[i]] == 'L':  # L
                        arg -= 1

            else:
                self.execute_command(com, arg)

            yield i, com, arg

            i += 2
