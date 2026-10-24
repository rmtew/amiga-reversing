"""Stale decoded/graph evidence cannot become APP proof just by being rehashed."""
import copy
import hashlib
import json

import pytest

from amiga_reversing.tools.pandora_passage_contract import validate_retained_inputs


def fixture():
    original=bytes.fromhex('4e714e75')
    rows=[dict(section_index=0,source_offset=i,size=2,bytes=original[i:i+2].hex()) for i in (0,2)]
    facts=[dict(section_index=0,source_offset=i,size=2,register_writes=[]) for i in (0,2)]
    fb=json.dumps(facts).encode();eb=json.dumps([dict(source_offset=0,target_offset=2)]).encode()
    receipt=dict(input_sha256=hashlib.sha256(original).hexdigest(),caller_contract=dict(proof=dict(
        facts_sha256=hashlib.sha256(fb).hexdigest(),edges_sha256=hashlib.sha256(eb).hexdigest())))
    return original,rows,facts,fb,eb,receipt


def test_exact_retained_input_is_accepted():
    original,rows,facts,fb,eb,receipt=fixture()
    assert validate_retained_inputs(original,rows,fb,eb,receipt)==(facts,json.loads(eb))


@pytest.mark.parametrize('change',['stale_facts','stale_graph','duplicate','coordinates','size','bytes'])
def test_retained_input_mutations_refuse_without_changing_row_count(change):
    original,rows,facts,fb,eb,receipt=fixture()
    if change=='stale_facts':
        facts[0]['register_writes']=['A6'];fb=json.dumps(facts).encode()
    elif change=='stale_graph':eb=json.dumps([dict(source_offset=0,target_offset=0)]).encode()
    elif change=='bytes':rows[0]['bytes']='4e75'
    else:
        if change=='duplicate':facts[1]['source_offset']=0
        elif change=='coordinates':facts[1]['source_offset']=4
        elif change=='size':facts[1]['size']=4
        fb=json.dumps(facts).encode()
        # Even a new review hash cannot hide duplicate/mismatched coordinates.
        receipt['caller_contract']['proof']['facts_sha256']=hashlib.sha256(fb).hexdigest()
    with pytest.raises(ValueError):validate_retained_inputs(original,rows,fb,eb,receipt)
