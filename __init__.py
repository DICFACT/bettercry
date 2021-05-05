from .modules.comp import compile_code as _cc

from .modules.vm import VirtualMachine as _VirtualMachine


def compile_code(code: str, scope: dict = None):
    return bytes(_cc(code, scope or {}, False))


def executes(code: str, mem_size: int = 14, out_size: int = 8):
    """Executes string containing BetterCry code"""
    compiled = compile_code(code)
    vm = VirtualMachine(mem_size, out_size)
    vm.execute(compiled)
    return vm


def execute(fp, mem_size: int = 14, out_size: int = 8):
    """Executes content of compiled BetterCry file (.bcc)"""
    vm = VirtualMachine(mem_size, out_size)
    vm.execute(fp.read())


class VirtualMachine(_VirtualMachine):
    pass
