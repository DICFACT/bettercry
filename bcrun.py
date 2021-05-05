import argparse
import os

from modules.comp import compile_code
from modules.vm import VirtualMachine


def main(path):
    if os.path.splitext(path)[1] == '.bc':
        with open(path) as file:
            program = bytes(compile_code(file.read(), {}))
    else:
        with open(path, 'rb') as file:
            program = file.read()
    vm = VirtualMachine()
    vm.execute(program)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser('Runs .bc and .bcc files')
    arg_parser.add_argument('infile', type=str, help='Path to better cry code')
    args = arg_parser.parse_args()

    main(args.infile)
