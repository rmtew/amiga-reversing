"""Execute bounded, source-mapped CPU recipes for media or decoded artifacts.

Input preparation owns provenance. This shared executor owns the closed action
contract and never supplies missing RAM or hardware values. Register startup
uses the witness seed; recipes cannot inject register values.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
from .c_backend import PROJECT_ROOT
from .mapped_execution import MappedExecution

MAX_BYTES = 32 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def integer(value, maximum=2**32-1):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError('invalid unsigned recipe integer')
    return value


def keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected.split()):
        raise ValueError('invalid recovery recipe fields')


def execute_actions(actions, memory_size, inputs, *, project_root=PROJECT_ROOT, register_seed=0):
    if not isinstance(actions, list) or len(actions) > 256:
        raise ValueError('recovery recipe exceeds operation bound')
    outputs, captures, runs = {}, [], []
    cpu = MappedExecution(integer(memory_size,16*1024*1024),project_root=project_root,register_seed=register_seed)
    for action in actions:
        if not isinstance(action,dict):
            raise ValueError('invalid recovery action')
        kind = action.get('op')
        if kind == 'load':
            keys(action,'op input address')
            if not isinstance(action['input'],str) or action['input'] not in inputs:
                raise ValueError('unknown recovery input')
            cpu.seed(integer(action['address']),inputs[action['input']])
        elif kind == 'run':
            keys(action,'op purpose start stop max_steps expected_stop writes')
            if not isinstance(action['purpose'],str) or not isinstance(action['writes'],list):
                raise ValueError('invalid execution scope')
            cpu.writable[:] = b'\0'*len(cpu.writable)
            for span in action['writes']:
                if not isinstance(span,list) or len(span) != 2:
                    raise ValueError('invalid write range')
                cpu.allow_write(integer(span[0]),integer(span[1]))
            run = cpu.run(integer(action['start']),integer(action['stop']),integer(action['max_steps']),expected_stop=action['expected_stop'])
            runs.append(dict(purpose=action['purpose'],**run))
        elif kind == 'capture':
            keys(action,'op file address size sha256')
            name = action['file']
            if (not isinstance(name,str) or not name.endswith('.bin') or '/' in name or '\\' in name or
                    Path(name).name != name or name in outputs):
                raise ValueError('invalid or duplicate output filename')
            size = integer(action['size'],MAX_BYTES)
            if sum(len(output) for output in outputs.values()) + size > MAX_BYTES:
                raise ValueError('recovery captures exceed output size bound')
            value = cpu.read(integer(action['address']),size)
            if digest(value) != action['sha256']:
                raise ValueError(f'captured artifact identity mismatch: {name}')
            outputs[name] = value
            captures.append(dict(file=name,size=len(value),sha256=digest(value),load_address=action['address'],after_run=len(runs)))
        else:
            raise ValueError('unsupported recovery action')
    return runs, captures, outputs


def recover_mapped(data: bytes, plan: dict, *, project_root: Path = PROJECT_ROOT, register_seed=0):
    keys(plan, 'schema_version kind source_sha256 memory_size evidence inputs actions')
    if (type(plan['schema_version']) is not int or plan['schema_version'] != 1 or
            plan['kind'] != 'mapped_cpu_recovery' or plan['source_sha256'] != digest(data)):
        raise ValueError('mapped recovery input identity mismatch')
    if not isinstance(plan['evidence'], str) or not isinstance(plan['inputs'], list) or len(plan['inputs']) > 32:
        raise ValueError('invalid recovery recipe collections')
    inputs, origins = {}, {}
    for item in plan['inputs']:
        keys(item, 'id offset size')
        name = item['id']
        if not isinstance(name, str) or not name or name in inputs:
            raise ValueError('duplicate or invalid recovery input identity')
        start, size = integer(item['offset']), integer(item['size'], MAX_BYTES)
        if not size or start + size > len(data):
            raise ValueError('mapped input outside source extent')
        value = data[start:start + size]
        inputs[name] = value
        origins[name] = dict(size=size, sha256=digest(value), source_ranges=[dict(source_offset=start, size=size)])
    runs, captures, outputs = execute_actions(plan['actions'], plan['memory_size'], inputs,
        project_root=project_root, register_seed=register_seed)
    return dict(schema_version=1, kind='mapped_cpu_recovery_result', source_sha256=digest(data),
        inputs=origins, runs=runs, captures=captures,
        scope='Original-instruction transformation under declared input/write bounds; not normal-path reachability'), outputs
