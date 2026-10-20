"""Bounded filtering of Copperline 1.0.0's documented full chip-bus records.

Format: https://github.com/CopperlineHQ/Copperline/blob/v1.0.0/docs/debugger/profiling.md
Raw sidecars stay in the owned local runtime directory; only requested ranges
are included in the report. No RAM baseline or screenshots are requested.
"""

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import tempfile

from .copperline_control import CopperlineError, CopperlineTimeout
from amiga_reversing.disasm.behaviour_validation import LoadedSource

LOADED_SOURCE=LoadedSource(__file__)

SLOT = struct.Struct('<HBBBBHIQI')
KINDS = {0: 'idle', 1: 'refresh', 2: 'cpu', 3: 'copper', 4: 'audio',
         5: 'blitter', 6: 'bitplane', 7: 'sprite', 8: 'disk', 9: 'conflict'}
MAX_MATCHES = 4096


def validate_bus_trace(spec):
    if (not isinstance(spec, dict) or set(spec) != {'frames', 'wait_seconds', 'ranges'}
            or type(spec['frames']) is not int or not 1 <= spec['frames'] <= 4
            or type(spec['wait_seconds']) is not int or not 1 <= spec['wait_seconds'] <= 30
            or not isinstance(spec['ranges'], list) or not 1 <= len(spec['ranges']) <= 4):
        raise ValueError('Chip-bus trace requires 1..4 frames, 1..30 seconds and 1..4 ranges')
    names = set()
    for item in spec['ranges']:
        if (not isinstance(item, dict) or set(item) != {'name', 'address', 'length'}
                or not isinstance(item['name'], str)
                or re.fullmatch(r'[a-z][a-z0-9_]{0,39}', item['name']) is None
                or item['name'] in names or type(item['length']) is not int
                or not 1 <= item['length'] <= 4096):
            raise ValueError('Chip-bus trace range requires a unique name and 1..4096 bytes')
        names.add(item['name'])
        address = item['address']
        absolute = type(address) is int and 0 <= address <= 0x1000000-item['length']
        relative = (isinstance(address, dict) and set(address) == {'base_register', 'offset'}
                    and isinstance(address['base_register'], str)
                    and re.fullmatch(r'a[0-7]', address['base_register']) is not None
                    and type(address['offset']) is int
                    and -0x1000000 < address['offset'] < 0x1000000)
        if not (absolute or relative):
            raise ValueError('Chip-bus trace address must be 24-bit or an a0..a7 binding')


def read_bus_profile(directory, ranges, max_frames):
    """Decode the fixed protocol format, preserving raw type/flags and limits."""
    LOADED_SOURCE.require_current()
    directory = Path(directory)
    if ((directory/'profile.json').stat().st_size > 2_000_000
            or (directory/'profile.jsonl').stat().st_size > 8_000_000):
        raise CopperlineError('Chip-bus profile metadata exceeds bounded capture size')
    summary = json.loads((directory/'profile.json').read_text())
    frames = [json.loads(line) for line in (directory/'profile.jsonl').read_text().splitlines()
              if line.strip()]
    if len(frames) != max_frames or any('marker' in f for f in frames):
        raise CopperlineError('Incomplete or repositioned chip-bus profile')
    records, counts, coverage, matched, scanned = [], Counter(), [], 0, 0
    for frame in frames:
        if frame.get('instantaneous_slots'):
            raise CopperlineError('Instantaneous transfers need explicit decoding; coverage is incomplete')
        rows, columns = frame.get('rows'), frame.get('line_cck')
        name = frame.get('slots_file')
        if (frame.get('traced') is not True or frame.get('slots_record_bytes') != SLOT.size
                or type(rows) is not int or not 1 <= rows <= 625
                or type(columns) is not int or not 1 <= columns <= 512
                or not isinstance(name, str)
                or re.fullmatch(r'slots-\d+-frame-\d+\.bin', name) is None):
            raise CopperlineError('Profile lacks bounded full chip-bus slot records')
        if (directory/name).stat().st_size != rows*columns*SLOT.size:
            raise CopperlineError('Chip-bus sidecar extent does not match raster geometry')
        raw = (directory/name).read_bytes()
        coverage.append({k: frame.get(k) for k in
                         ['frame', 'seconds', 'retired', 'pc', 'traced', 'partial', 'rows',
                          'line_cck', 'cck_length', 'blits']})
        coverage[-1].update(slots_sha256=hashlib.sha256(raw).hexdigest(), slots_bytes=len(raw))
        for index, (reg, kind, subtype, size, ipl, flags, address, data, events) in enumerate(SLOT.iter_unpack(raw)):
            scanned += 1
            if not 1 <= size <= 8:
                continue
            names = [r['name'] for r in ranges
                     if address < r['address']+r['length'] and address+size > r['address']]
            if not names:
                continue
            engine, access = KINDS.get(kind, 'unknown'), 'write' if flags & 1 else 'read'
            matched += 1
            for label in names:
                counts[(label, engine, access)] += 1
            if len(records) < MAX_MATCHES:
                records.append(dict(frame=frame['frame'], row=index//columns, hpos=index%columns,
                                    ranges=names, kind=kind, engine=engine, subtype=subtype,
                                    size=size, address=address, data=f'0x{data:016x}', reg=reg,
                                    ipl=ipl, flags=flags, events=events, access=access))
    return dict(profile_summary={k: summary.get(k) for k in
                                ['version', 'started', 'ended', 'frames_written', 'samples_dropped']},
                frames=coverage, scanned_slots=scanned, matching_transfers=matched,
                records=records, omitted_matching_records=matched-len(records),
                counts=[dict(range=r, engine=e, access=a, transfers=n)
                        for (r, e, a), n in sorted(counts.items())])


def capture_bus_trace(client, spec, start_event, directory):
    validate_bus_trace(spec)
    if not isinstance(start_event, dict) or type(start_event.get('frame')) is not int:
        raise ValueError('Chip-bus trace requires a canonical anchor frame event')
    if directory is None:
        raise ValueError('Chip-bus trace requires an owned runtime directory')
    regs, ranges = client.registers(), []
    for item in spec['ranges']:
        address = item['address']
        if isinstance(address, dict):
            address = regs[address['base_register']]+address['offset']
        if not 0 <= address <= 0x1000000-item['length']:
            raise ValueError('Resolved chip-bus trace range exceeds 24-bit memory')
        ranges.append(dict(item, address=address))
    output = Path(tempfile.mkdtemp(prefix='chip-bus-', dir=directory)).resolve()
    request = dict(path=str(output), frames=spec['frames'], slots=True, memory=False,
                   screenshots='none', pc_samples=True)
    result = dict(requested_trace=spec, ranges=ranges, start_event=start_event,
                  profile_request=request, status='unavailable')
    try:
        result['profile_start'] = client.request('profile.start', request)
    except CopperlineError as exc:
        result['error'] = str(exc)
        return result
    try:
        try:
            result['stop_event'] = client.run_until(
                {'frame': start_event['frame']+spec['frames']+1}, timeout=spec['wait_seconds'])
            result['status'] = 'captured' if result['stop_event'].get('reason') == 'target' else 'not_hit'
        except CopperlineTimeout as exc:
            result.update(status='timeout', stop_event=exc.stop_event,
                          deadline_recovery=dict(resume_stop=exc.stop_event, pause_stop=exc.pause_event))
    finally:
        # Failure here aborts the session rather than leaving an active capture.
        result['profile_stop'] = client.request('profile.stop')
    try:
        result['profile'] = read_bus_profile(output, ranges, spec['frames'])
    except (OSError, ValueError, CopperlineError) as exc:
        result.update(status='unavailable', error=str(exc))
    return result
