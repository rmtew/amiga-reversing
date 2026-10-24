"""A matching final buffer cannot hide a wrong observed read or interference."""
import copy
import pytest
from amiga_reversing.tools.pandora_body_dma_audit import compare_windows,SIZE

BASE=0xf5a8

def windows():
    def report(access,count):
        return dict(profile_summary={'samples_dropped':0},omitted_matching_records=0,frames=[],
            records=[dict(engine='blitter',ranges=['new'],access=access,address=BASE+2*i,
                          size=2,data=hex(i),frame=1 if access=='write' else 2) for i in range(count)])
    return report('write',SIZE//2),report('read',SIZE//2)


def test_full_and_explicitly_partial_consumer_coverage():
    a,b=windows();result=compare_windows(a,b,BASE)
    assert result['status']=='observed_values_match' and result['unobserved_consumer_words']==0
    b['records']=b['records'][:-4];result=compare_windows(a,b,BASE)
    assert result['consumer_reads']==1148 and result['unobserved_consumer_words']==4


def test_wrong_consumer_value_is_mismatch():
    a,b=windows();b['records'][4]['data']='0xffff'
    result=compare_windows(a,b,BASE)
    assert result['status']=='mismatch' and result['mismatch_count']==1


@pytest.mark.parametrize('bad',['unknown_read','old_address','interference','loss','truncated','missing_write','duplicate_read','wrong_order'])
def test_incomplete_or_interfering_evidence_refuses(bad):
    a,b=windows()
    if bad=='unknown_read':b['records'][0]['address']=BASE+SIZE
    elif bad=='old_address':b['records'][0]['ranges']=['old']
    elif bad=='interference':b['records'][0]['access']='write'
    elif bad=='loss':b['profile_summary']['samples_dropped']=1
    elif bad=='truncated':b['omitted_matching_records']=1
    elif bad=='duplicate_read':b['records'][1]=copy.deepcopy(b['records'][0])
    elif bad=='wrong_order':b['records'][0]['frame']=0
    else:a['records'].pop()
    with pytest.raises(ValueError):compare_windows(a,b,BASE)
