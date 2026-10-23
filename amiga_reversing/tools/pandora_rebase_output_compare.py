"""Strict offline comparison for the explicit Pandora capture experiment.

Run by pathname with Python + Pillow. No media is emitted. Comparison requires
actual matching handoff/phase/input clocks; it does not fit offsets, resample,
mask pixels, or apply audio tolerances. Capture files remain private.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

CCK_HZ = 3_546_895
FRAME_CCK = 71_051


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    with path.open('rb') as stream:
        result = hashlib.file_digest(stream, 'sha256')
    return result.hexdigest()


def wav_info(path):
    """Accept the emulator's PCM float WAV, including extensible float format."""
    with path.open('rb') as stream:
        require(stream.read(4) == b'RIFF', 'Not RIFF PCM')
        stream.read(4)
        require(stream.read(4) == b'WAVE', 'Not WAVE PCM')
        fmt = None
        while header := stream.read(8):
            require(len(header) == 8, 'Truncated WAV chunk')
            kind, size = struct.unpack('<4sI', header)
            if kind == b'fmt ':
                require(16 <= size <= 64, 'Unsupported WAV format extent')
                fmt = stream.read(size)
            elif kind == b'data':
                require(fmt is not None and len(fmt) >= 16, 'Missing WAV format')
                tag, channels, rate, _, block, bits = struct.unpack_from('<HHIIHH', fmt)
                if tag == 0xFFFE:
                    require(len(fmt) == 40 and struct.unpack_from('<I', fmt, 24)[0] == 3,
                            'Extensible WAV is not IEEE float')
                else:
                    require(tag == 3, 'WAV is not IEEE float')
                require(channels == 2 and bits == 32 and block == 8 and rate == 44100,
                        'Unsupported capture sample format')
                offset = stream.tell()
                require(size > 0 and size % block == 0 and offset + size <= path.stat().st_size,
                        'Incomplete WAV sample data')
                return dict(rate=rate, channels=channels, block=block, bits=bits,
                            offset=offset, data_bytes=size, frames=size // block)
            else:
                stream.seek(size, 1)
            if size % 2:
                stream.seek(1, 1)
    raise ValueError('Missing WAV data')


def pcm_interval(original, candidate, start_cck, end_cck):
    a, b = wav_info(original), wav_info(candidate)
    require({k: a[k] for k in ('rate', 'channels', 'block', 'bits')} ==
            {k: b[k] for k in ('rate', 'channels', 'block', 'bits')}, 'PCM formats differ')
    start = -(-start_cck * a['rate'] // CCK_HZ)
    end = end_cck * a['rate'] // CCK_HZ
    require(0 <= start < end <= min(a['frames'], b['frames']), 'PCM interval unavailable')
    hashes = [hashlib.sha256(), hashlib.sha256()]
    mismatch = None
    with original.open('rb') as x, candidate.open('rb') as y:
        x.seek(a['offset'] + start * a['block'])
        y.seek(b['offset'] + start * b['block'])
        remaining = (end - start) * a['block']
        consumed = 0
        while remaining:
            n = min(1_048_576, remaining)
            left, right = x.read(n), y.read(n)
            require(len(left) == len(right) == n, 'Truncated PCM interval')
            hashes[0].update(left)
            hashes[1].update(right)
            if mismatch is None and left != right:
                i = next(i for i, (u, v) in enumerate(zip(left, right)) if u != v)
                mismatch = start + (consumed + i) // a['block']
            consumed += n
            remaining -= n
    return dict(status='pass' if mismatch is None else 'mismatch', format=a,
                start_cck=start_cck, end_cck=end_cck, start_sample=start,
                end_sample=end, compared_stereo_frames=end-start,
                compared_float_samples=2*(end-start), first_different_sample=mismatch,
                original_interval_sha256=hashes[0].hexdigest(),
                candidate_interval_sha256=hashes[1].hexdigest(),
                alignment='Identical captured emulated clock; no shift/resampling/tolerance.')


def asset_and_dma_checks(original, candidate, reports, target):
    """Byte integrity and explicit device source bounds, without guessing words."""
    assets = json.loads((target/'source-package-manifest.json').read_text())['manifest']['files']
    before = (original/'experiment.bin').read_bytes()
    after = (candidate/'experiment.bin').read_bytes()
    raw = []
    for item in assets:
        if item.get('kind') != 'asset':
            continue
        start, size = item['source_offset'], item['size']
        require(item['source_section_index'] == 0 and before[start:start+size] == after[start:start+size],
                'Asset bytes differ: '+item['path'])
        require(hashlib.sha256(after[start:start+size]).hexdigest() == item['sha256'], 'Asset manifest hash differs')
        if item.get('classification') != 'opaque_data':
            require(start+size <= 0x55370, 'Known asset outside moved prefix')
        raw.append(dict(path=item['path'], offset=start, size=size, sha256=item['sha256']))
    # The original initializer consumes eleven length/divisor/payload records.
    cursor = 0x4EAD8
    primary = []
    for index in range(11):
        length = int.from_bytes(before[cursor:cursor+4], 'big')
        divisor = int.from_bytes(before[cursor+4:cursor+6], 'big')
        start = cursor+6
        require(0 < length < 0x10000 and divisor > 0 and start+length <= 0x55370, 'Bad audio record')
        require(before[cursor:start+length] == after[cursor:start+length], 'Audio header/payload differs')
        primary.append(dict(index=index, offset=start, size=length,
                            sha256=hashlib.sha256(after[start:start+length]).hexdigest()))
        cursor = start+length
    require(cursor == 0x5500A and before[cursor:0x552CA] == after[cursor:0x552CA], 'Silence/secondary bank differs')
    require(before[0x4D5DE:0x4D7DE] == after[0x4D5DE:0x4D7DE], 'Blank sprite bytes differ')
    audio = [(p['offset'], p['offset']+p['size']) for p in primary]+[(0x5500A,0x5504A),(0x5504A,0x552CA)]
    slot = struct.Struct('<HBBBBHIQI')
    devices = {3:'copper',4:'audio',5:'blitter',6:'bitplane',7:'sprite'}
    observations = []
    event_streams = []
    for directory, report in zip((original,candidate), reports):
        base = report['config']['assembly_base']
        streams = {}
        for capture in report['output_observations']['dma']:
            phase = capture['phase']
            folder = directory/('dma-ending' if phase == 'post_ending' else 'dma-'+phase)
            metadata = [json.loads(line) for line in (folder/'profile.jsonl').read_text().splitlines()]
            wanted = {f['frame']:f for f in capture['frames']}
            counts = {name:0 for name in devices.values()}
            stream = []
            violations = []
            ranges = {
                'copper':[(base,base+0x55370)],
                'blitter':[(0,0x100000)],  # Physical Chip RAM only; not per-object bounds.
                'audio':[(base+a,base+b) for a,b in audio],
                'sprite':[(base+0x4D5DE,base+0x4D7DE),(0x65370,0x653F8)],
                'bitplane':[(0x70000,0x77D00),(0x78000,0x7D000)],
            }
            for ordinal, frame in enumerate(f for f in metadata if f['frame'] in wanted):
                require(not frame.get('partial'), 'Partial DMA frame')
                sidecar = folder/frame['slots_file']
                require(digest(sidecar) == wanted[frame['frame']]['slots_sha256'], 'DMA evidence changed')
                for i, item in enumerate(slot.iter_unpack(sidecar.read_bytes())):
                    reg, kind, subtype, size, ipl, flags, address, data, events = item
                    if kind not in devices or not 1 <= size <= 8:
                        continue
                    engine = devices[kind]
                    counts[engine] += 1
                    if not any(a <= address and address+size <= b for a,b in ranges[engine]):
                        violations.append(dict(engine=engine,address=address,width=size,frame=frame['frame'],
                                               subtype=subtype,reg=reg,data=data,row=i//frame['line_cck'],hpos=i%frame['line_cck']))
                    if engine in ('audio','sprite','bitplane'):
                        normalized = ('image',address-base) if base <= address < base+0x55370 else ('fixed',address)
                        stream.append((ordinal,i//frame['line_cck'],i%frame['line_cck'],engine,subtype,size,normalized,data))
            streams[phase] = stream
            observations.append(dict(layout='original' if base == 0x10000 else 'relocated',phase=phase,
                                     frames=sorted(wanted),counts=counts,violations=violations))
        event_streams.append(streams)
    comparisons = {name:event_streams[0][name] == event_streams[1][name] for name in event_streams[0]}
    findings_a = [v for o in observations if o['layout']=='original' for v in o['violations']]
    findings_b = [v for o in observations if o['layout']=='relocated' for v in o['violations']]
    # Keep these outside the certified asset bounds. The original and moved
    # streams both fetch zero POS/CTL words through NULL SPR0/1 pointers before
    # cursor installation; this is not a license to admit arbitrary bad pointers.
    legacy = (len(findings_a)==len(findings_b)==8 and findings_a==findings_b
              and all(v['engine']=='sprite' and v['address'] in (0,2) and v['width']==2
                      and v['data']==0 and v['subtype'] in (0,1)
                      and v['reg'] in (0x140,0x142,0x148,0x14A) for v in findings_a))
    no_findings = not findings_a and not findings_b
    return dict(status='pass' if (no_findings or legacy) and all(comparisons.values()) else 'mismatch',
                target_bounds_status='original_null_sprite_controls_outside_asset_bounds' if legacy else 'pass' if no_findings else 'mismatch',
                original_bounds_findings=findings_a, candidate_bounds_findings=findings_b,
                new_bounds_findings=[] if findings_a==findings_b else findings_b,
                bounds_scope='Audio: eleven payloads/silence/secondary bank; sprite: blank/cursor buffers; bitplane: fixed display banks; Copper: copied image; blitter: physical Chip RAM only.',
                raw_assets=raw, raw_asset_bytes=sum(x['size'] for x in raw), primary_audio_payloads=primary,
                silence_and_secondary_bytes=0x552CA-0x5500A, blank_sprite_bytes=512,
                observations=observations, exact_audio_sprite_bitplane_streams=comparisons,
                limits=['DMA bounds/streams are six complete sampled frames per layout, not whole-route DMA coverage.',
                        'Raw asset checks exclude pointer tables and instruction operands; actual source-edit groups are enumerated in the build config.',
                        'Opaque file suffix remains loader-only under original prefix-copy semantics; all known graphics/audio assets lie in the verified moved prefix.'])


def compare(original, candidate, title_original, title_candidate, target):
    from PIL import Image  # Explicit local prerequisite; never silently skipped.

    paths = [original, candidate, title_original, title_candidate]
    reports = [json.loads((p/'report.json').read_text()) for p in paths]
    a, b, ta, tb = reports
    require(a['status'] == 'saved_earth_and_escaped_original_control' and
            b['status'] == 'saved_earth_and_escaped_relocated_cold_boot', 'Incomplete cold route')
    require(a['config']['profile'] == b['config']['profile'], 'Machine profiles differ')
    require(a['config']['original_control'] and b['config']['matched_startup'], 'Wrong build modes')
    require(a['payload_sha256'] == a['config']['original_binary_sha256'], 'Original was modified')
    require(b['native_materialization']['full_prefix_verified'], 'Moved prefix not verified')
    fixture_a, fixture_b = a['boot_phase_fixture'], b['boot_phase_fixture']
    require(fixture_a['stop']['cck'] == fixture_b['stop']['cck'] and
            fixture_a['registers'] == fixture_b['registers'], 'Boot clock/CPU fixture differs')
    phases_a, phases_b = a['scenario']['phases'], b['scenario']['phases']
    require(len(phases_a) == len(phases_b) == 576, 'Missing route phases')
    for x, y in zip(phases_a, phases_b):
        require(x['name'] == y['name'] and x['status'] == y['status'] == 'hit', 'Phase mismatch')
        require(x['stop_event']['cck'] == y['stop_event']['cck'], 'Phase clock mismatch: '+x['name'])
        require(int(y['pc'], 0)-int(x['pc'], 0) == 0x70000, 'Runtime PC mapping differs')
    def inputs(report):
        return [(r['method'], r['arguments'], r['cleanup'], r['outcome'],
                 r['anchor']['phase'], r['anchor']['stop']['cck']) for r in report['scenario']['input_trace']]
    require(inputs(a) == inputs(b), 'Controller inputs or clocks differ')
    for report in (a, b):
        counters = report['loss_monitor']['counters']
        require(counters['events'] > 0 and counters['dropped_events'] ==
                counters['dropped_notifications'] == 0, 'Incomplete event coverage')
    images = []
    image_a={x['phase']:x for x in a['output_observations']['screenshots']}
    image_b={x['phase']:x for x in b['output_observations']['screenshots']}
    cases = [(original, candidate, row['phase'], row['capture']['path'])
             for row in a['output_observations']['screenshots']]
    for left_dir, right_dir, name, filename in cases:
        # Capture paths in private reports are never trusted as publication paths.
        image_name = Path(filename).name
        left_path, right_path = left_dir/image_name, right_dir/image_name
        with Image.open(left_path) as x, Image.open(right_path) as y:
            x, y = x.convert('RGBA'), y.convert('RGBA')
            same = x.size == y.size and x.tobytes() == y.tobytes()
            images.append(dict(state=name, status='pass' if same else 'mismatch',
                               original_frame=image_a[name]['frame'],candidate_frame=image_b[name]['frame'],
                               original_size=list(x.size), candidate_size=list(y.size),
                               original_sha256=digest(left_path), candidate_sha256=digest(right_path)))
    require(ta['status'] == tb['status'] == 'bounded_output_prefix_complete' and
            ta['title_no_input_hold_frames'] == tb['title_no_input_hold_frames'] == 180,
            'Settled title prerequisite missing')
    require(ta['scenario']['phases'][0]['stop_event']['cck'] ==
            tb['scenario']['phases'][0]['stop_event']['cck'], 'Title state clocks differ')
    with Image.open(title_original/'title_menu_loop.png') as x, Image.open(title_candidate/'title_menu_loop.png') as y:
        x, y = x.convert('RGBA'), y.convert('RGBA')
        images.append(dict(state='settled_title_180_frames',original_frame=ta['scenario']['phases'][0]['stop_event']['frame'],candidate_frame=tb['scenario']['phases'][0]['stop_event']['frame'], status='pass' if x.size == y.size and
                           x.tobytes() == y.tobytes() else 'mismatch', dimensions=list(x.size),
                           original_sha256=digest(title_original/'title_menu_loop.png'),
                           candidate_sha256=digest(title_candidate/'title_menu_loop.png')))
    # A predeclared interval includes the complete game and 20 post-ending frames.
    # The capture itself continues 30 frames. No post-hoc waveform fitting/cropping.
    start_cck = fixture_a['stop']['cck']
    end_cck = (a['ending']['final_frame']+20)*FRAME_CCK
    require(a['ending']['final_frame'] == b['ending']['final_frame'], 'Ending frame differs')
    pcm = pcm_interval(original/'mixed-audio.wav', candidate/'mixed-audio.wav', start_cck, end_cck)
    integrity = asset_and_dma_checks(original,candidate,(a,b),target)
    wa,wb=wav_info(original/'mixed-audio.wav'),wav_info(candidate/'mixed-audio.wav')
    require(wa['frames']==wb['frames'],'Recorded PCM extents differ')
    eof_cck=-(-wa['frames']*CCK_HZ//wa['rate'])
    full_pcm=pcm_interval(original/'mixed-audio.wav',candidate/'mixed-audio.wav',start_cck,eof_cck)
    full_pcm['end_bound']='Entire equal-length recorded PCM to EOF; no fitted crop.'
    return dict(schema='pandora-output-comparison-v1',
                status=('pass_with_original_bounds_findings' if integrity['original_bounds_findings'] else 'pass') if pcm['status'] == full_pcm['status'] == integrity['status'] == 'pass' and all(x['status'] == 'pass' for x in images) else 'mismatch',
                profile=a['config']['profile'], matched_phases=576,
                matched_controller_calls=len(inputs(a)), boot_release_cck=start_cck,
                report_sha256=[digest(p/'report.json') for p in paths],
                images=images, PCM=pcm, PCM_to_EOF=full_pcm, asset_and_DMA_integrity=integrity,
                limits=['Representative frames only; not every frame/optional path.',
                        'Pre-game ROM/disk audio before common handoff is excluded explicitly.',
                        'Custom direct-payload cold boot/ECS profile, not original packed-disk/OCS parity.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('original', 'candidate', 'title-original', 'title-candidate', 'target', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    tool_sha=digest(Path(__file__))
    result = compare(args.original, args.candidate, args.title_original, args.title_candidate, args.target)
    require(digest(Path(__file__))==tool_sha,'Comparison tool changed during execution')
    result['comparison_tool_sha256']=tool_sha
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ('status', 'matched_phases', 'matched_controller_calls')}))
    raise SystemExit(0 if result['status'] in ('pass','pass_with_original_bounds_findings') else 1)


if __name__ == '__main__':
    main()
