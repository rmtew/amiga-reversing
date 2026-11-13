"""Bounded native CPU execution over explicitly initialized source ranges.

This is a CPU witness, not a machine emulator. Unknown reads/fetches, hardware
accesses and writes outside declared ranges stop execution. Python supplies
bytes, bounds and provenance; the existing generated C simulator executes the
unaltered 68000 instructions, including self-modifying decoders.
"""
from __future__ import annotations
import ctypes as C
from pathlib import Path
from .c_backend import PROJECT_ROOT, _platform_disk_dll


class Diag(C.Structure):
    _fields_ = [('severity', C.c_uint32), ('code', C.c_uint32), ('message', C.c_char * 512)]


class Diags(C.Structure):
    _fields_ = [('count', C.c_size_t), ('dropped_count', C.c_size_t), ('items', Diag * 8)]

    def error(self):
        return next((d.message.decode() for d in self.items[:self.count] if d.severity == 3), '')


class BufferResult(C.Structure):
    _fields_ = [('data', C.c_void_p), ('size', C.c_size_t), ('diagnostics', Diags)]


class Cpu(C.Structure):
    _fields_ = [('d', C.c_uint32*8), ('a', C.c_uint32*8), ('c', C.c_uint32*32),
                ('pc', C.c_uint32), ('sr', C.c_uint16)]


class WriteRange(C.Structure):
    _fields_ = [('start', C.c_uint32), ('end', C.c_uint32)]


class Trace(C.Structure):
    _fields_ = [('step_count', C.c_size_t), ('start_pc', C.c_uint32), ('stop_pc', C.c_uint32),
                ('memory_write_start', C.c_uint32), ('memory_write_end', C.c_uint32),
                ('memory_write_count', C.c_size_t), ('memory_write_range_count', C.c_size_t),
                ('memory_write_range_overflow', C.c_uint8), ('reserved', C.c_uint8*7),
                ('memory_write_ranges', WriteRange*32), ('stop_reason', C.c_int), ('diagnostics', Diags)]


Access = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_uint8, C.c_uint32, C.c_uint8, C.c_uint32)


class Observer(C.Structure):
    _fields_ = [('access', Access), ('user', C.c_void_p)]


def assemble_stx_sectors(data: bytes, index_pairs: list[tuple[int, int]], max_size: int,
                         project_root: Path = PROJECT_ROOT) -> bytes:
    """Use the native reader once for the whole ordered sector assembly."""
    if (not index_pairs or len(index_pairs) > 65536 or type(max_size) is not int or
            not 0 < max_size <= 32*1024*1024 or
            any(not isinstance(pair,(tuple,list)) or len(pair) != 2 for pair in index_pairs) or
            any(type(v) is not int or not 0 <= v < 2**32 for pair in index_pairs for v in pair)):
        raise ValueError('invalid bounded STX assembly')
    dll = _platform_disk_dll(project_root)
    dll.platform_disk_extract_stx_sectors_buffer.argtypes = [C.c_void_p, C.c_size_t,
        C.POINTER(C.c_uint32), C.c_size_t, C.c_size_t]
    dll.platform_disk_extract_stx_sectors_buffer.restype = BufferResult
    source = C.create_string_buffer(data)
    pairs = (C.c_uint32*(2*len(index_pairs)))(*(v for p in index_pairs for v in p))
    result = dll.platform_disk_extract_stx_sectors_buffer(source, len(data), pairs, len(index_pairs), max_size)
    try:
        if result.diagnostics.error():
            raise ValueError(result.diagnostics.error())
        if not result.data:
            raise ValueError('native STX assembly returned no bytes')
        return C.string_at(result.data, result.size)
    finally:
        dll.platform_disk_free_bytes(result.data)


class MappedExecution:
    def __init__(self, size: int, *, project_root: Path = PROJECT_ROOT, register_seed: int = 0):
        if type(size) is not int or not 0 < size <= 16*1024*1024:
            raise ValueError('invalid execution memory size')
        self.memory = (C.c_uint8*size)()
        self.known = bytearray(size)
        self.writable = bytearray(size)
        self.cpu = Cpu()
        for i in range(8):
            self.cpu.d[i] = self.cpu.a[i] = (register_seed + i*0x1020304) & 0xffffffff
        self.cpu.sr = 0x2700
        self.failed = False
        self.dll = _platform_disk_dll(project_root)
        self.dll.m68k_simulate_run_concrete_observed.argtypes = [C.c_uint8, C.c_void_p, C.c_size_t,
            C.POINTER(Cpu), C.c_size_t, C.c_uint32, C.c_uint32, C.c_void_p,
            C.POINTER(Observer), C.POINTER(Trace)]
        self.dll.m68k_simulate_run_concrete_observed.restype = C.c_int

    def _span(self, address: int, size: int):
        if type(address) is not int or type(size) is not int or address < 0 or size < 0 or address+size > len(self.memory):
            raise ValueError('mapped range outside execution memory')
        return address, address+size

    def seed(self, address: int, data: bytes):
        if self.failed: raise ValueError('failed execution state cannot be reused')
        start,end = self._span(address,len(data))
        self.memory[start:end] = data
        self.known[start:end] = b'\1'*len(data)

    def allow_write(self, address: int, size: int):
        start,end = self._span(address,size)
        self.writable[start:end] = b'\1'*size

    def read(self, address: int, size: int) -> bytes:
        if self.failed: raise ValueError('failed execution state cannot be reused')
        start,end = self._span(address,size)
        if not all(self.known[start:end]):
            raise ValueError('output contains unknown bytes')
        return bytes(self.memory[start:end])

    def run(self, start_pc: int, stop_pc: int, max_steps: int, *, expected_stop='pc') -> dict:
        if self.failed: raise ValueError('failed execution state cannot be reused')
        self._span(start_pc,2)
        if (type(stop_pc) is not int or not 0 <= stop_pc < len(self.memory) or
                type(max_steps) is not int or not 0 < max_steps <= 2_000_000 or expected_stop not in {'pc','limit'}):
            raise ValueError('invalid execution bound')
        failures = []
        def access(_user, kind, address, width, value):
            if (kind not in (0,1,2) or (kind == 2 and not 0 < width <= 32) or
                    (kind != 2 and width not in (1,2,4)) or address+width > len(self.memory)):
                failures.append((kind,address,width,'outside mapped RAM')); return 0
            end = address+width
            mask = self.writable if kind == 1 else self.known
            if not all(mask[address:end]):
                failures.append((kind,address,width,'forbidden write' if kind == 1 else 'unknown read/fetch')); return 0
            if kind == 1: self.known[address:end] = b'\1'*width
            return 1
        observer = Observer(Access(access),None)
        trace = Trace()
        self.cpu.pc = start_pc
        rc = self.dll.m68k_simulate_run_concrete_observed(0,self.memory,len(self.memory),C.byref(self.cpu),
            max_steps,stop_pc,stop_pc+1,None,C.byref(observer),C.byref(trace))
        if rc or failures or trace.stop_reason != (1 if expected_stop == 'pc' else 3):
            self.failed = True
            raise ValueError(f'native CPU witness failed at ${trace.stop_pc:x}: {failures[:1]} {trace.diagnostics.error()} (stop {trace.stop_reason})')
        return dict(start_pc=trace.start_pc,stop_pc=trace.stop_pc,steps=trace.step_count,
                    stop='pc' if trace.stop_reason == 1 else 'instruction_limit',
                    writes=trace.memory_write_count)
