"""Decoded artifacts use the same closed original-instruction action contract."""
import copy
from pathlib import Path
import pytest
from amiga_reversing.disasm.mapped_recipe import digest, recover_mapped
from tests.test_game_catalog import family


def fixture():
    data=bytes.fromhex('23fc11223344000020004ef900003000')
    plan=dict(schema_version=1,kind='mapped_cpu_recovery',source_sha256=digest(data),memory_size=0x4000,
        evidence='synthetic original immediate store and jump',inputs=[dict(id='code',offset=0,size=len(data))],
        actions=[dict(op='load',input='code',address=0x1000),
            dict(op='run',purpose='execute original bytes',start=0x1000,stop=0x3000,max_steps=8,expected_stop='pc',writes=[[0x2000,4]]),
            dict(op='capture',file='decoded.bin',address=0x2000,size=4,sha256=digest(bytes.fromhex('11223344')))])
    return data,plan


def test_source_slice_executes_original_instructions_and_retains_mapping():
    data,plan=fixture()
    report,outputs=recover_mapped(data,plan,register_seed=0xdeadbeef)
    assert outputs=={'decoded.bin':bytes.fromhex('11223344')}
    assert report['inputs']['code']['source_ranges']==[dict(source_offset=0,size=len(data))]
    assert report['runs'][0]['steps']==2
    assert recover_mapped(data,plan)[1]==outputs


@pytest.mark.parametrize('mutation',[
    lambda p:p.update(kind='stx_cpu_recovery'),
    lambda p:p.update(source_sha256='0'*64),
    lambda p:p['inputs'][0].update(offset=1),
    lambda p:p['inputs'][0].update(size=0),
    lambda p:p['inputs'].append(copy.deepcopy(p['inputs'][0])),
    lambda p:p['actions'][1].update(writes=[]),
    lambda p:p['actions'][1].update(registers={'d0':0}),
    lambda p:p['actions'][-1].update(sha256='0'*64),
])
def test_unproven_inputs_writes_and_register_injection_are_refused(mutation):
    data,plan=fixture();mutation(plan)
    with pytest.raises(ValueError):recover_mapped(data,plan)


def test_mapped_derivation_materializes_through_the_catalog(family,monkeypatch):
    from amiga_reversing.disasm import game_catalog as catalog
    import json
    root,value,_,_,_=family
    data,plan=fixture();source=digest(data);output=plan['actions'][-1]['sha256']
    value['artifacts']={source:dict(size=len(data),role='stored source'),output:dict(size=4,role='decoded')}
    value['sources']={source:dict(kind='private_media',format='bytes')}
    value['releases']['st']['media']=[source]
    value['targets']['st_program']['artifact']=output
    value['targets']['st_program']['context']['phase']='decoded_snapshot'
    recipe=root/'decode.json';recipe.write_text(json.dumps(plan))
    value['derivations']={'decode':dict(kind=plan['kind'],input=source,recipe='decode.json',recipe_sha256=digest(recipe.read_bytes()),outputs={'decoded.bin':output})}
    (root/'games/fixture.json').write_text(json.dumps(value))
    private=root/'input.bin';private.write_bytes(data);catalog.bind_source(root,'fixture',source,private)
    monkeypatch.setenv('AMIGA_C_BACKEND_DLL_ROOT',str(Path(__file__).resolve().parents[1]))
    assert catalog.materialize(root,'fixture',output).read_bytes()==bytes.fromhex('11223344')
