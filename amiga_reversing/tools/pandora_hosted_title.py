"""Bounded settled-title capture at the original foreground-loop instruction.

No inputs, state writes or fitted delay. Frame2700 snapshots can stop mid-star;
this observes the first original loop entry at least180 physical frames after
its first entry. Every intervening visit executes naturally. The owned emulator
is terminated after capture; this prefix does not claim an OS cleanup/return.
"""
import hashlib
import json
from amiga_reversing.tools.pandora_OS_application import observe_game
from amiga_reversing.tools.pandora_layout_runtime import summarize_dma


class TitleCaptured(Exception):
    pass


class TitleCapture:
    # Normal vasm listing of canonical reference: service_foreground_title_iteration.
    # The original instruction is BSR.W update_starfield, source $FD2.
    SOURCE_OFFSET = 0xfd2

    def __call__(self, client, base, labels, native, out, record):
        pc = 0x80000+self.SOURCE_OFFSET
        breakpoint = client.add_breakpoint(pc)
        first = None
        for visit in range(4096):
            if client.registers()['pc'] == pc:
                stepped = client.request('step', dict(n=1))
                if stepped.get('reason') != 'step':
                    raise ValueError('Title instruction departure failed')
            stop = client.run_until(dict(frame=2000), timeout=20)
            if client.registers()['pc'] != pc or stop.get('reason') != 'breakpoint':
                raise ValueError('Original title helper not observed within bounds')
            if first is None:
                first = stop
            if stop['frame'] >= first['frame']+180:
                break
        else:
            raise ValueError('Title did not advance180 frames within4096 original loop visits')
        client.remove_breakpoint(breakpoint)
        owners = {m['region_id']:m['runtime_address'] for m in native['layout']['items'][0]['regions']}
        image = out/'settled-title.png'
        client.request('capture.screenshot', dict(path=str(image), native=True))
        state = dict(first_stop=first, stop=stop, visits=visit+1, source_offset=self.SOURCE_OFFSET,
            registers=client.registers(), PRNG_bytes=client.read_memory(owners['pandora_prng_state'],8).hex(),
            title_stars_sha256=hashlib.sha256(client.read_memory(owners['pandora_title_stars'],1000)).hexdigest(),
            screenshot_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
            input_count=0, guest_state_writes=0)
        record('anchored_title', **state)
        directory=out/'dma-title'
        client.request('profile.start', dict(path=str(directory),frames=3,slots=True,
            memory=False,screenshots='none',pc_samples=True))
        end=client.run_until(dict(frame=stop['frame']+5),timeout=15)
        if end.get('reason')!='target':
            raise ValueError('Incomplete finite title DMA window')
        client.request('profile.stop')
        image_region=next(r for r in native['layout']['items'][0]['regions'] if r['region_kind']=='image')
        record('title_DMA', **summarize_dma(directory,dict(image_region,
            runtime_regions=native['layout']['items'][0]['regions'])))
        raise TitleCaptured


def observe_title(out, rom, copperline, actual_validator, *, audio_stems=None):
    try:
        observe_game(out,rom,copperline,actual_validator,route=TitleCapture(),audio_stems=audio_stems)
    except TitleCaptured:
        result=json.loads((out/'live.json').read_text())
        result.update(status='bounded_original_helper_settled_title_and_DMA_capture',
            limits=['No controller input or guest-state injection. No clock fitting.',
                'Prefix observation only; emulator stopped after capture, not a game OS-return test.',
                'Three DMA frames captured, two complete frames classified; not all-route DMA coverage.'])
        (out/'live.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    raise ValueError('Settled title capture did not reach its explicit boundary')
