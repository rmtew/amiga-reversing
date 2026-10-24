"""Pandora's existing completion route under the DOS observer's owned lifecycle.

This is an observer/input adapter, not a placement engine. The native actual
plan supplies all address mappings. Synchronous CPU guards exclude live leases;
no DMA/all-fetch coverage or proof of unused storage is implied.
"""
import copy
import hashlib
import json
from amiga_reversing.tools.copperline_runtime import run_scenario, _run_scenario_phase
from amiga_reversing.tools.observed_layout_mapping import observed_address
from amiga_reversing.tools.pandora_layout_runtime import ending_outcome


class HostedRoute:
    def __init__(self, scenario):
        self.scenario = scenario
        self.report = None

    def __call__(self, client, base, labels, native, out, record):
        plan = native['layout']['items'][0]
        def moved(address, size=1):
            return observed_address(plan, address, size)
        scenario = copy.deepcopy(self.scenario)
        view = dict(base_addr=0x80000, source_start=0, source_end=0x55370,
            runtime_base=0x80000, execution_view_id='native-hosted-actual-six-owner')
        def update(read):
            address = read.get('address')
            if address is not None:
                read['address'] = moved(address, read.get('size', 1))
            if 'expect_hex' in read and address in (0x3b9a, 0x3b9e, 0x3bba):
                data = bytearray.fromhex(read['expect_hex'])
                if len(data) >= 4:
                    data[:4] = moved(int.from_bytes(data[:4], 'big')).to_bytes(4, 'big')
                read['expect_hex'] = data.hex()
        for phase in scenario['phases']:
            phase.update(breakpoint_address=0x80000+phase['source_offset'], runtime_view=view)
            for read in phase.get('capture', {}).get('memory_reads', []):
                update(read)
            if 'until_memory' in phase:
                update(phase['until_memory'])
        scenario.setdefault('symbols', {})['runtime_view'] = view
        for function in scenario['symbols'].get('functions', []):
            function.update(runtime_start=0x80000+function['source_start'],
                runtime_end=0x80000+function['source_end'])
        (out/'runtime-scenario.json').write_text(json.dumps(scenario, indent=2)+'\n')
        live = native['leases'] + native['fixed_leases_requiring_OS_acquisition']
        candidates = [(r['original_address'], r['size']) for r in plan['regions']
            if not r.get('parent_region_id') and r['original_address'] != r['runtime_address']]
        candidates.append((0x300, 42))
        spans = []
        for address, size in candidates:
            remaining = [(address, address+size)]
            for item in live:
                start, end = item['address'], item['address']+item['size']
                next_spans = []
                for lo, hi in remaining:
                    if end <= lo or start >= hi:
                        next_spans.append((lo, hi))
                    else:
                        if lo < start:
                            next_spans.append((lo, start))
                        if end < hi:
                            next_spans.append((end, hi))
                remaining = next_spans
            spans.extend(remaining)
        merged = []
        for lo, hi in sorted(spans):
            if merged and lo <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(hi, merged[-1][1]))
            else:
                merged.append((lo, hi))
        guards = [client.request('break.add', dict(kind='mmio', addr=lo, len=hi-lo, access='access'))['id']
            for lo, hi in merged]
        guards += [client.add_breakpoint(address) for address in (0x10000, 0x1046a, 0x300)]
        record('guards', ranges=merged, excluded_live_leases=live, CPU_only=True,
            all_fetches=False, start='before original world initialization, after early bootstrap/workspace setup')
        loss = dict(events=0, dropped_notifications=0, dropped_events=0)
        queue = client.events
        class Sink:
            def append(self, message):
                if message.get('method') == 'event.mmio':
                    data = message['params']
                    loss['events'] += 1
                    for key in ('dropped_notifications', 'dropped_events'):
                        if type(data.get(key)) is not int or data[key] < 0:
                            raise ValueError('Missing or invalid event-loss counter')
                        loss[key] = max(loss[key], data[key])
                queue.append(message)
            def __iter__(self):
                return iter(queue)
        client.events = Sink()
        client.request('events.subscribe', dict(events=['mmio'],
            mmio=[dict(addr=moved(0x3b9a, 4), len=4, access='write')]))
        count, media = 0, []
        identity = out/'identity-payload.bin'
        identity.write_bytes(client.read_memory(0x20000, 0x5c000))
        def capture(name, frame):
            image = out/(name+'.png')
            client.request('capture.screenshot', dict(path=str(image), native=True))
            media.append(dict(phase=name, frame=frame, sha256=hashlib.sha256(image.read_bytes()).hexdigest()))
        def progress(*args, **kwargs):
            nonlocal count
            result = _run_scenario_phase(*args, **kwargs)
            count += 1
            event = result.get('stop_event') or {}
            row = dict(number=count, name=result['name'], status=result['status'],
                frame=event.get('frame'), pc=result.get('pc'))
            with (out/'progress.jsonl').open('a') as stream:
                stream.write(json.dumps(row)+'\n')
            if count % 10 == 0 or result['status'] != 'hit':
                print('PHASE', json.dumps(row), flush=True)
            if result['status'] == 'hit' and result['name'] in (
                    'title_menu_loop', 'ui_overlay_initialization', 'initial_proximity_context',
                    'entry_officer_card_transferred', 'ei_sonicdriver_hit_1', 'ac_console_ready'):
                capture(result['name'], event['frame'])
            return result
        result = run_scenario(client, scenario, identity, trace_directory=out, phase_runner=progress)
        (out/'scenario-result.json').write_text(json.dumps(result, indent=2)+'\n')
        if len(result['phases']) != 576 or not all(p['status'] == 'hit' for p in result['phases']):
            raise ValueError('Incomplete original completion route; retain failure evidence')
        ending = ending_outcome(result, 0x80000, 0x55370, address_mapper=moved)
        capture('saved_earth_escape', ending['final_frame'])
        record('ending', **ending)
        deadline = ending['final_frame']+4000
        terminal = client.add_breakpoint(base+labels['game_DMA_quiescent'])
        stop = client.run_until(dict(frame=deadline), timeout=120)
        if client.registers()['pc'] != base+labels['game_DMA_quiescent']:
            raise ValueError('Natural ending exit not observed within bounds')
        client.remove_breakpoint(terminal)
        if not loss['events'] or loss['dropped_notifications'] or loss['dropped_events']:
            raise ValueError('Incomplete heartbeat/event evidence')
        client.request('events.unsubscribe', dict(events=['mmio']))
        client.events = queue
        for guard in guards:
            client.remove_breakpoint(guard)
        self.report = dict(ending=ending, screenshots=media, loss=loss,
            scenario_sha256=hashlib.sha256(json.dumps(scenario, sort_keys=True).encode()).hexdigest(),
            phases=576, status='saved_earth_escape_natural_exit_observed')
        record('route', **self.report)
        return stop, deadline
