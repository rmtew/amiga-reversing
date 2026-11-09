"""Original silo choice reads after PRNG return, with supplied random values.

These cases qualify mask/BYTE-read/WORD publication, not spawn eligibility,
PRNG distribution, object capacity, lifetime or normal-game reachability.
"""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,INPUT,STACK

CHOICES={0xB43A:(13,18,21,31,32,33,34,45),0xB442:(1,9,15,39)}


@pytest.mark.parametrize('entry,table',[(0xA036,0xB43A),(0xA924,0xB43A),
    (0xA300,0xB442),(0xAA6C,0xB442)])
@pytest.mark.parametrize('random_value',list(range(8))+[0xFFFF,0x8000,0x12345678,0xFFFF0007])
def test_masked_choice_is_published_as_word_type(original_image,memory,entry,table,random_value):
    raw=original_image[0];choices=CHOICES[table];ground=table==0xB442
    assert tuple(raw[table-4096:table-4096+len(choices)])==choices
    expected_code=bytes.fromhex('024000034243163100003483'if ground else'02400007103100003480')
    assert raw[entry-4096:entry-4096+len(expected_code)]==expected_code
    m=memory;cpu=state(m,entry);cpu.a[1]=table;cpu.a[2]=INPUT
    cpu.d[0]=random_value;cpu.d[3]=0xFEDC9876
    put(m,INPUT,0xDEADBEEF)
    run(original_image,m,cpu,{entry+len(expected_code)})
    selected=choices[random_value&(len(choices)-1)]
    assert get(m,INPUT)==(selected<<16)|0xBEEF
    assert cpu.a[1]==table and cpu.a[2]==INPUT and cpu.a[7]==STACK
    if ground:
        assert cpu.d[0]==(random_value&0xFFFF0000)|(random_value&3)
        assert cpu.d[3]==0xFEDC0000|selected
    else:
        assert cpu.d[0]==(random_value&0xFFFF0000)|selected
        assert cpu.d[3]==0xFEDC9876
