from amiga_reversing.tools.pandora_app_usage_closure import reachable


def test_native_call_and_return_edges_do_not_invent_post_return_flow():
    code={0:dict(flow='sequential',size=2),2:dict(flow='call',size=2),
          4:dict(flow='return',size=2),6:dict(flow='sequential',size=2),
          20:dict(flow='sequential',size=2),22:dict(flow='return',size=2)}
    edges=[dict(source_offset=2,target_offset=20,status='resolved',kind='call'),
           dict(source_offset=2,target_offset=4,status='resolved',kind='fallthrough')]
    assert reachable(code,edges,[0])=={0,2,4,20,22}


def test_unresolved_transfer_needs_explicit_reviewed_target_and_missing_nodes_stay_missing():
    code={0:dict(flow='jump',size=2),2:dict(flow='return',size=2)}
    edges=[dict(source_offset=0,target_offset=None,status='unresolved',kind='jump')]
    assert reachable(code,edges,[0])=={0}
    reviewed=edges+[dict(source_offset=0,target_offset=2,status='resolved',kind='jump'),
                    dict(source_offset=0,target_offset=100,status='resolved',kind='jump')]
    assert reachable(code,reviewed,[0])=={0,2}
