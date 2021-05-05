import argparse
import os

from modules.vm import VirtualMachine
from modules.getch import getch


OUT_BUFFER_SIZE = 8
MEMORY_SIZE = 14


COMS = '\0^\'GB+-*/%N?=LW!PRA><#FI'
DESCRIPTIONS = [
    '',
    'Sets given VALUE to BUFFER',
    'Sends given VALUE to OUTPUT BUFFER',
    'Goes to VALUE labels forward, only if BUFFER not 0',
    'Goes to VALUE labels back, only if BUFFER not 0',
    'Adds given VALUE to BUFFER',
    'Subtracts given VALUE from BUFFER',
    'Multiplies BUFFER by given VALUE',
    'Calculates integer part of division BUFFER on VALUE',
    'Calculates remaining of division BUFFER on VALUE',
    'Generates pseudo random number between 0 and VALUE',
    'Compares BUFFER and VALUE (0-less or equal, 1-greater)',
    'Compares BUFFER and VALUE (1-equal, 0-not equal)',
    'Label for G and B functions, do noting for itself',
    'Writes value from BUFFER to current MEMORY cell',
    'Inverts BUFFER value (!0 -> 0, 0 -> 1)',
    'Sets current position in MEMORY block to BUFFER',
    'Reads value from current MEMORY cell to BUFFER',
    'Goes to MEMORY cell (within block) specified in BUFFER',
    'Goes to next MEMORY cell',
    'Goes to previous MEMORY cell',
    'Sends BUFFER value to OUTPUT BUFFER',
    'Prints OUTPUT BUFFER on screen',
    'Waits for user to input a char and writes it code to BUFFER'
]


def byte(i: int, f: int = 2):
    return hex(i)[2:].zfill(f).upper()


def render_com(com, arg):
    c = COMS[com]
    if com == 1 and 32 <= arg < 127 or com == 2:
        return c + chr(arg)
    elif com == 1:
        return c + byte(arg)
    elif 3 <= com <= 12:
        return c + (byte(arg, 1) if arg != 16 else '.')
    elif com == 0:
        return '[B]'
    else:
        return c


def print_header(file):
    print('FILE -------------------------------------------------------------------------')
    print(f'N: {file}')


def print_mem(memory, address):
    print('MEMORY -----------------------------------------------------------------------')
    print(f'[{byte(address & 255)}]', end=' ')
    p = 8
    for i in range(24):
        d = i + address - p
        if d < 0 or d > len(memory):
            print('   ', end='')
        elif d == 0:
            print(f'[{byte(memory[d])}', end='')
        elif d == len(memory):
            print(']', end='')
            break
        elif d % 256 == 0:
            print(f'|{byte(memory[d])}', end='')
        else:
            print(f' {byte(memory[d])}', end='')
    print()
    print(f'B: {address // 256}  (A: {address})'.ljust(5 + p * 3, ' '), '^' + (f"'{chr(memory[address])}'" if 32 <= memory[address] < 127 else ''))


def print_program(buf, program, i):
    print('PROGRAM ----------------------------------------------------------------------')
    com, arg = program[i:i+2]
    c_com = render_com(com, arg)

    lp = ''
    bias = 0
    while len(lp) < 30:
        bias -= 2
        if i + bias < 0:
            break
        c, a = program[i+bias:i+bias+2]
        lp = render_com(c, a) + ' ' + lp
    lp = lp.rjust(30, ' ')[-30:]

    rp = ''
    bias = 0
    while len(rp) < 48 - len(c_com):
        bias += 2
        if i + bias >= len(program):
            break
        c, a = program[i+bias:i+bias+2]
        rp = rp + ' ' + render_com(c, a)
    rp = rp[:48-len(c_com)]

    print(lp + c_com + rp)

    print(f'BYTE: {i}'.ljust(30, ' '), f'^  [{byte(buf)}]', sep='')
    # 0^'GB+-*/%N?=L~W!PRA><#FI|
    if COMS[com] in '+-*/%?=':  # Действие совершается над буфером
        print(f'OP: BUF <= {byte(buf)} {COMS[com]} {byte(arg)}')
    elif COMS[com] in '^N':  # Запись в буфер
        print(f'OP: BUF <= {COMS[com]} {byte(arg)}')
    elif COMS[com] in 'GB':
        print(f'OP: {COMS[com]} {byte(arg)} ACT: {"SKIP" if not buf else "GOTO"}')
    elif COMS[com] == '\'':
        print(f'OP: {COMS[com]} {arg}')
    else:
        print(f'OP: {COMS[com]}')
    print(f'D: {DESCRIPTIONS[com]}')


def print_output(output, carriage, printed):
    print('OUTPUT -----------------------------------------------------------------------')
    out = output[:output.find(0)]
    out = ''.join((chr(i) if 32 <= i < 127 else ' ') for i in out[carriage-50:carriage]) + 'I'
    print('O:', out)
    print('vvv --------------------------------------------------------------------------')
    print(printed)


class InputWrapper:
    def __init__(self):
        pass

    def read(self, _):
        return getch()


class OutputWrapper:
    def __init__(self):
        self.content = ''

    def write(self, val):
        self.content += val


def print_all(file_name, vm, program, i, output):
    os.system('cls')
    print_header(file_name)
    print_mem(vm.memory, vm.address)
    print_program(vm.buffer, program, i)
    print_output(vm.output, vm.carriage, output.content)


def main(path):
    if os.path.splitext(path)[1] == '.bc':
        from modules.comp import compile_code
        with open(path) as file:
            program = compile_code(file.read(), {})
            file_name = file.name
    else:
        with open(path, 'rb') as file:
            program = bytearray(file.read())
            file_name = file.name

    input_ = InputWrapper()
    output = OutputWrapper()
    vm = VirtualMachine(mem_size=MEMORY_SIZE, out_buffer_size=OUT_BUFFER_SIZE, input_=input_, output=output)

    debugging = False

    for i, com, arg in vm.execute_by_step(program):
        if debugging:
            print('\nPress any to step or "Enter" to continue...', end='')
            ch = getch()
            if ord(ch) == 3:  # ctrl+c
                break
            elif ord(ch) == 13:  # Enter
                debugging = False
                continue

            print_all(file_name, vm, program, i, output)

        elif com == 0:
            print_all(file_name, vm, program, i, output)
            debugging = True


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser('Runs .bcc files in debug mode')
    arg_parser.add_argument('infile', type=str, help='Path to compiled better cry code')
    args = arg_parser.parse_args()

    main(args.infile)
