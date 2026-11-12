"""Preserve conflict semantics/order while avoiding unrelated range pairs."""
import random
from itertools import combinations

import pytest

from amiga_reversing.disasm import manual_actions as ma


def seed(identity,kind,start,end,hunk=0):
    return {'seed_id':identity,'kind':kind,'hunk':hunk,'addr':start,'end':end}


def pairwise_reference(seeds):
    items=[]
    for left,right in combinations(seeds.values(),2):
        li,ri=left.get('seed_id'),right.get('seed_id');lk,rk=left.get('kind'),right.get('kind')
        a,b=ma._manual_seed_range(left),ma._manual_seed_range(right)
        if not isinstance(li,str) or not isinstance(ri,str) or not isinstance(lk,ma.ManualSeedKind) or not isinstance(rk,ma.ManualSeedKind) or a is None or b is None:continue
        if not ma._manual_seed_required(left) or not ma._manual_seed_required(right) or lk==rk:continue
        if a[0]!=b[0] or a[1]>=b[2] or b[1]>=a[2]:continue
        items.append({'kind':ma.ReviewItemKind.MANUAL_SEED_CONFLICT,
            'item_id':f'manual_seed_conflict:{min(li,ri)}:{max(li,ri)}',
            'scope':ma.ReviewItemScope.RANGE,'state':ma.ReviewItemState.OPEN,'review_blocker':True,
            'seed_ids':[li,ri],'hunk':a[0],'start':max(a[1],b[1]),'end':min(a[2],b[2]),
            'message':f'Required manual seeds {li} and {ri} conflict'})
    return items


def test_nested_touching_disjoint_and_same_kind_ranges_keep_insertion_order():
    C,D=ma.ManualSeedKind.CODE,ma.ManualSeedKind.DATA
    values=[seed('z',C,10,30),seed('a',D,20,25),seed('b',D,0,10),seed('c',C,15,19),
            seed('d',D,0,100),seed('e',D,15,16,1),seed('f',C,100,101),
            {'seed_id':'g','kind':D,'range':'h0:15..15'}, {'seed_id':'bad','kind':'data','addr':10}]
    data={str(i):v for i,v in enumerate(values)}
    result=ma._manual_seed_conflict_items(data)
    assert result==pairwise_reference(data)
    assert [r['seed_ids']for r in result]==[['z','a'],['z','d'],['z','g'],['c','d'],['c','g']]


@pytest.mark.parametrize('random_seed',range(20))
def test_conflicts_match_pairwise_oracle_for_reordered_multi_hunk_ranges(random_seed):
    rng=random.Random(random_seed);values=[]
    for i in range(80):
        start=rng.randrange(-20,60)
        values.append(seed(str(i),rng.choice(list(ma.ManualSeedKind)),start,start+rng.randrange(-2,40),rng.randrange(3)))
    rng.shuffle(values);data={str(i):value for i,value in enumerate(values)}
    assert ma._manual_seed_conflict_items(data)==pairwise_reference(data)


def test_large_nonoverlap_set_parses_each_range_once(monkeypatch):
    original=ma._manual_seed_range;calls=[]
    def counted(value):calls.append(value['seed_id']);return original(value)
    monkeypatch.setattr(ma,'_manual_seed_range',counted)
    data={str(i):seed(str(i),list(ma.ManualSeedKind)[i%2],4*i,4*i+4)for i in range(4000)}
    assert ma._manual_seed_conflict_items(data)==[]
    assert len(calls)==len(data)
