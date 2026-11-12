"""Bounded retired-PC counters from Copperline 1.0.0's CLCV format.

https://github.com/CopperlineHQ/Copperline/blob/v1.0.0/docs/debugger/profiling.md#guest-coverage
Counts discover execution sites; source identity additionally needs matching
bytes and absence of bus writes throughout the same capture window.
"""
import hashlib
from pathlib import Path
import struct
from .copperline_control import CopperlineError
from amiga_reversing.disasm.behaviour_validation import LoadedSource

LOADED_SOURCE = LoadedSource(__file__)
MAX_CODE_BYTES = 1024 * 1024
U32 = struct.Struct('<I')


def bind_coverage_view(payload_path, view):
    LOADED_SOURCE.require_current()
    if not isinstance(view, dict):
        raise ValueError('Retired coverage needs the verified canonical runtime view')
    base, start, end = (view.get(k) for k in ['base_addr', 'source_start', 'source_end'])
    raw = Path(payload_path).read_bytes()
    if (type(view.get('section_index', 0)) is not int or view.get('section_index', 0) != 0 or any(type(v) is not int for v in [base, start, end])
            or not 0 <= start < end <= len(raw) or (base | start | end) & 1
            or end - start > MAX_CODE_BYTES or not 0 <= base <= 0x1000000 - (end-start)):
        raise ValueError('Retired coverage needs one aligned, bounded canonical file view')
    return dict(base=base, size=end-start, source_start=start,
                payload_sha256=hashlib.sha256(raw).hexdigest())


def read_retired_coverage(path, binding):
    """Return sparse counters for local analysis; never embed them in a report."""
    LOADED_SOURCE.require_current()
    path = Path(path)
    base, size = binding['base'], binding['size']
    if (type(base) is not int or type(size) is not int or base & 1 or size & 1
            or not 2 <= size <= MAX_CODE_BYTES or not 0 <= base <= 0x1000000-size):
        raise ValueError('Invalid retired-coverage binding')
    expected = 12 + 12 + 4*(size//2) + 4 + 16
    if path.stat().st_size != expected:
        raise CopperlineError('Retired coverage has an unexpected sidecar extent')
    raw = path.read_bytes()
    if raw[:4] != b'CLCV' or U32.unpack_from(raw, 4)[0] != 1 or U32.unpack_from(raw, 8)[0] != 1:
        raise CopperlineError('Unsupported retired-coverage header')
    if struct.unpack_from('<III', raw, 12) != (base, size, size//2):
        raise CopperlineError('Retired coverage does not match the requested code view')
    counters = {}; total_in = 0
    for i, (count,) in enumerate(struct.iter_unpack('<I', raw[24:24+size*2])):
        if count == 0xffffffff:
            raise CopperlineError('Saturated retired counter cannot establish complete coverage')
        if count:
            counters[base+2*i] = count
            total_in += count
    position = 24 + size*2
    if U32.unpack_from(raw, position)[0] != 0:
        raise CopperlineError('Unexpected sparse addresses outside the requested code view')
    outside, total = struct.unpack_from('<QQ', raw, position+4)
    if total_in + outside != total:
        raise CopperlineError('Retired-coverage totals are inconsistent')
    return dict(counters=counters, inside_retired=total_in, outside_retired=outside,
                total_retired=total, distinct_pcs=len(counters), path=str(path.resolve()),
                bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def before_coverage(client, payload_path, view, ranges):
    binding = bind_coverage_view(payload_path, view)
    raw = Path(payload_path).read_bytes(); windows = []
    for item in ranges:
        address, size = item['address'], item['length']
        # This runner fixes A500 Chip RAM to 512 KiB. Chip-bus absence
        # cannot establish write absence for CPU-only slow/fast memory.
        if address < 0 or address+size > 512*1024:
            raise ValueError('Retired identity windows require the configured 512 KiB Chip RAM')
        if not binding['base'] <= address <= binding['base']+binding['size']-size:
            raise ValueError('Retired-coverage bus windows must lie inside the canonical view')
        source = binding['source_start'] + address-binding['base']
        expected = raw[source:source+size]
        observed = client.read_memory(address, size)
        windows.append(dict(name=item['name'], address=address, size=size, source_start=source,
                            source_sha256=hashlib.sha256(expected).hexdigest(),
                            before_sha256=hashlib.sha256(observed).hexdigest(),
                            before_matches=observed == expected))
    return binding, windows


def finish_coverage(client, output, payload_path, binding, windows, bus_profile):
    LOADED_SOURCE.require_current()
    raw = Path(payload_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != binding['payload_sha256']:
        raise CopperlineError('Canonical payload changed during retired coverage')
    result = read_retired_coverage(Path(output)/'coverage.bin', binding)
    counters = result.pop('counters')
    for item in windows:
        observed = client.read_memory(item['address'], item['size'])
        item['after_sha256'] = hashlib.sha256(observed).hexdigest()
        item['after_matches'] = item['after_sha256'] == item['source_sha256']
        item['bus_writes'] = sum(row['transfers'] for row in bus_profile['counts']
                                if row['range'] == item['name'] and row['access'] == 'write')
        item['retired_instructions'] = sum(n for pc, n in counters.items()
                                          if item['address'] <= pc < item['address']+item['size'])
        item['distinct_pcs'] = sum(item['address'] <= pc < item['address']+item['size'] for pc in counters)
        item['source_bytes_stable'] = item['before_matches'] and item['after_matches'] and not item['bus_writes']
    result.update(runtime_binding=binding, windows=windows,
                  identity_scope='only matching windows without bus writes; other PCs are discovery candidates')
    return result
