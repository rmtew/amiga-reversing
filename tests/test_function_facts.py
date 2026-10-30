from __future__ import annotations

import pytest

from amiga_reversing.disasm import function_facts


class _Projection:
    labels = (
        {"name": "first", "addr": 0x10200, "address_domain": "runtime"},
        {"name": "second", "addr": 0x10220, "address_domain": "runtime"},
    )


def test_function_facts_own_multiple_blocks_and_reject_overlap(monkeypatch) -> None:
    monkeypatch.setattr(function_facts, "load_manual_projection", lambda *_: _Projection())
    monkeypatch.setattr(function_facts, "resolve_project_paths", lambda _: type("Paths", (), {"target_dir": None})())
    analysis = {"sections": [{"blocks": [
        {"start_offset": 0x200, "end_offset": 0x204},
        {"start_offset": 0x204, "end_offset": 0x208},
        {"start_offset": 0x220, "end_offset": 0x224},
    ], "edges": [
        {"source_block_index": 0, "target_block_index": 1, "kind": 1},
        {"source_block_index": 2, "target_block_index": 1, "kind": 1},
    ]}]}

    result = function_facts.canonical_function_facts("unused", analysis, {"base_addr": 0x10000, "source_start": 0, "source_end": 0x400})

    assert [(item["name"], item["status"], item.get("reason")) for item in result["functions"]] == [
        ("first", "rejected", "overlapping_cfg_ownership"),
        ("second", "rejected", "overlapping_cfg_ownership"),
    ]


def test_function_facts_keep_shared_return_block(monkeypatch) -> None:
    monkeypatch.setattr(function_facts, "load_manual_projection", lambda *_: _Projection())
    monkeypatch.setattr(function_facts, "resolve_project_paths", lambda _: type("Paths", (), {"target_dir": None})())
    analysis = {"sections": [{"blocks": [
        {"start_offset": 0x200, "end_offset": 0x204},
        {"start_offset": 0x204, "end_offset": 0x208},
        {"start_offset": 0x220, "end_offset": 0x224},
    ], "edges": [
        {"source_block_index": 0, "target_block_index": 1, "kind": 1},
        {"source_block_index": 2, "target_block_index": 1, "kind": 1},
        {"source_block_index": 1, "target_block_index": 0xFFFFFFFF, "kind": 5},
    ]}]}

    result = function_facts.canonical_function_facts("unused", analysis, {"base_addr": 0x10000, "source_start": 0, "source_end": 0x400})

    assert [item["status"] for item in result["functions"]] == ["accepted", "accepted"]
    assert result["functions"][0]["shared_terminal_blocks"] == [{"start_offset": 0x204, "end_offset": 0x208}]


def test_function_facts_record_all_cfg_owned_blocks(monkeypatch) -> None:
    monkeypatch.setattr(function_facts, "load_manual_projection", lambda *_: _Projection())
    monkeypatch.setattr(function_facts, "resolve_project_paths", lambda _: type("Paths", (), {"target_dir": None})())
    analysis = {"sections": [{"blocks": [
        {"start_offset": 0x200, "end_offset": 0x204},
        {"start_offset": 0x204, "end_offset": 0x208},
        {"start_offset": 0x220, "end_offset": 0x224},
    ], "edges": [
        {"source_block_index": 0, "target_block_index": 1, "kind": 1},
    ]}]}

    result = function_facts.canonical_function_facts("unused", analysis, {"base_addr": 0x10000, "source_start": 0, "source_end": 0x400})

    first, second = result["functions"]
    assert first["status"] == "accepted"
    assert first["ranges"] == [{"start_offset": 0x200, "end_offset": 0x208}]
    assert first["owned_blocks"] == [
        {"start_offset": 0x200, "end_offset": 0x204},
        {"start_offset": 0x204, "end_offset": 0x208},
    ]
    assert second["status"] == "accepted"
    assert second["ranges"] == [{"start_offset": 0x220, "end_offset": 0x224}]


def test_function_facts_reject_unresolved_flow_target(monkeypatch) -> None:
    monkeypatch.setattr(function_facts, "load_manual_projection", lambda *_: _Projection())
    monkeypatch.setattr(function_facts, "resolve_project_paths", lambda _: type("Paths", (), {"target_dir": None})())
    analysis = {"sections": [{"blocks": [{"start_offset": 0x200, "end_offset": 0x204}], "edges": [
        {"source_block_index": 0, "target_block_index": 0xFFFFFFFF, "kind": 4},
    ]}]}

    result = function_facts.canonical_function_facts("unused", analysis, {"base_addr": 0x10000, "source_start": 0, "source_end": 0x400})

    assert result["functions"][0]["reason"] == "unresolved_cfg_flow_target"
    assert result["functions"][0]["evidence"] == {"entry": "manual_label", "ownership": "rejected_cfg_flow"}


def test_function_facts_reject_multiple_names_for_one_entry(monkeypatch) -> None:
    projection = type("Projection", (), {"labels": (
        {"name": "first_name", "addr": 0x10200, "address_domain": "runtime"},
        {"name": "second_name", "addr": 0x10200, "address_domain": "runtime"},
    )})()
    monkeypatch.setattr(function_facts, "load_manual_projection", lambda *_: projection)
    monkeypatch.setattr(function_facts, "resolve_project_paths", lambda _: type("Paths", (), {"target_dir": None})())
    analysis = {"sections": [{"blocks": [{"start_offset": 0x200, "end_offset": 0x204}], "edges": []}]}

    result = function_facts.canonical_function_facts("unused", analysis, {"base_addr": 0x10000, "source_start": 0, "source_end": 0x400})

    assert [(item["name"], item["reason"]) for item in result["functions"]] == [
        ("first_name", "ambiguous_entry_names"),
        ("second_name", "ambiguous_entry_names"),
    ]


def test_function_facts_reject_named_entry_inside_owned_block(monkeypatch) -> None:
    projection = type("Projection", (), {"labels": (
        {"name": "outer", "addr": 0x10200, "address_domain": "runtime"},
        {"name": "interior", "addr": 0x10202, "address_domain": "runtime"},
    )})()
    monkeypatch.setattr(function_facts, "load_manual_projection", lambda *_: projection)
    monkeypatch.setattr(function_facts, "resolve_project_paths", lambda _: type("Paths", (), {"target_dir": None})())
    analysis = {"sections": [{"blocks": [{"start_offset": 0x200, "end_offset": 0x204}], "edges": []}]}

    result = function_facts.canonical_function_facts("unused", analysis, {"base_addr": 0x10000, "source_start": 0, "source_end": 0x400})

    assert [(item["name"], item["reason"]) for item in result["functions"]] == [
        ("outer", "named_entry_inside_owned_block"),
        ("interior", "entry_not_accepted_block"),
    ]


def test_analysis_functions_use_entries_not_labels_and_cover_sections() -> None:
    analysis = {"sections": [
        {"section_index": 0, "blocks": [
            {"start_offset": 0, "end_offset": 4, "certainty": 1},
            {"start_offset": 4, "end_offset": 8, "certainty": 1},
            {"start_offset": 16, "end_offset": 20, "certainty": 1},
        ], "code_start_refs": [{"offset": 0, "reason_name": "section_entry"}],
         "symbol_origins": [{"offset": 4, "symbol_name": "interior_label"},
                            {"offset": 16, "symbol_name": "manual_callee", "origin_kind": "manual_label"}],
         "edges": [
             {"source_block_index": 0, "target_block_index": 2, "source_offset": 0, "target_offset": 16, "kind": 3},
             {"source_block_index": 0, "target_block_index": 1, "source_offset": 0, "target_offset": 4, "kind": 1},
             {"source_block_index": 1, "target_block_index": 0xFFFFFFFF, "source_offset": 4, "target_offset": 0xFFFFFFFF, "kind": 4},
             {"source_block_index": 2, "target_block_index": 0xFFFFFFFF, "source_offset": 16, "target_offset": 0xFFFFFFFF, "kind": 5},
         ]},
        {"section_index": 2, "blocks": [{"start_offset": 0, "end_offset": 2}], "edges": [],
         "code_start_refs": [{"offset": 0, "reason_name": "policy_entry_point"}]},
    ]}
    result = function_facts.analysis_function_facts("test", analysis)
    first, callee, other = result["functions"]
    assert [(f["section_index"], f["entry_offset"]) for f in result["functions"]] == [(0, 0), (0, 16), (2, 0)]
    assert first["ranges"] == [{"start_offset": 0, "end_offset": 8}]
    assert first["ownership_status"] == "partial"
    assert first["callees"][0]["target_offset"] == 16
    assert first["unresolved_transfers"][0]["kind"] == "jump"
    assert callee["name"] == "manual_callee"
    assert callee["callers"][0]["source_entries"] == [0]
    assert callee["unresolved_transfers"] == []  # Dynamic returns are expected.
    assert other["name"] is None
    assert "native_cfg_is_section_local" in result["unknowns"]


def test_analysis_functions_retain_unsupported_and_shared_candidates() -> None:
    result = function_facts.analysis_function_facts("test", {"sections": [{
        "section_index": 0,
        "blocks": [{"start_offset": 0, "end_offset": 2}, {"start_offset": 4, "end_offset": 6},
                   {"start_offset": 8, "end_offset": 10}],
        "code_start_refs": [{"offset": x, "reason_name": "policy_entry_offset"} for x in (0, 4, 12)],
        "edges": [{"source_block_index": i, "target_block_index": 2, "source_offset": x,
                   "target_offset": 8, "kind": 4} for i, x in enumerate((0, 4))],
    }]})
    first, second, unavailable = result["functions"]
    assert first["ownership_status"] == second["ownership_status"] == "ambiguous"
    assert first["shared_block_starts"] == [8]
    assert unavailable["ownership_status"] == "unavailable"
    assert unavailable["ranges"] == []
    assert "entry_not_accepted_block" in unavailable["unknowns"]


def test_analysis_function_resolved_offset_without_block_is_partial() -> None:
    result = function_facts.analysis_function_facts("test", {"sections": [{
        "section_index": 0,
        "blocks": [{"start_offset": 0, "end_offset": 2}],
        "code_start_refs": [{"offset": 0, "reason_name": "section_entry"}],
        "edges": [{"source_block_index": 0, "target_block_index": 0xFFFFFFFF,
                   "source_offset": 0, "target_offset": 8, "kind": 4}],
    }]})
    fact = result["functions"][0]
    assert fact["ownership_status"] == "partial"
    assert "flow_target_not_accepted_block" in fact["unknowns"]


def test_analysis_function_names_use_frozen_source_labels_without_adding_entries():
    analysis = {"sections": [{"section_index": 0,
        "blocks": [{"start_offset": 0, "end_offset": 4}], "edges": [],
        "code_start_refs": [{"offset": 0, "reason_name": "section_entry"}],
        "symbol_origins": [{"offset": 0, "symbol_name": "loc_0_00000000"},
                           {"offset": 2, "symbol_name": "interior"}]}]}
    calls = []
    def symbol(name, **changes):
        return dict(name=name, provenance="typed_render_declaration", declaration_kind=1,
                    name_is_generated=False,
                    section_index=0, source_offset=0,
                    source_symbol=dict(section_index=0, source_offset=0), **changes)
    good = symbol("restored_entry")
    equate = symbol("not_a_label"); equate["declaration_kind"] = 2
    wrong_domain = symbol("same_number_elsewhere"); wrong_domain["source_symbol"] = dict(section_index=1, source_offset=0)
    interior = symbol("not_an_entry"); interior["source_offset"] = 2
    def query(**options):
        calls.append(options)
        assert options["section_index"] == 0 and options["source_offset"] == 0
        if options["offset"] == 0:
            return dict(items=[equate, wrong_domain, interior], has_more=True)
        assert options["offset"] == 3
        return dict(items=[good], has_more=False)
    before = function_facts.analysis_function_facts("test", analysis)
    after = function_facts.analysis_function_facts("test", analysis, artifact_query=query)
    assert len(after["functions"]) == 1
    entry = after["functions"][0]
    assert entry["name"] == "restored_entry"
    assert entry["names"] == ["loc_0_00000000", "restored_entry"]
    assert entry["name_evidence"][-1] == good
    for key in before["functions"][0].keys() - {"name", "names", "name_evidence"}:
        assert entry[key] == before["functions"][0][key]
    assert len(calls) == 2


def test_analysis_function_symbol_pagination_refuses_no_progress():
    analysis = {"sections": [{"section_index": 0, "blocks": [], "edges": [],
        "code_start_refs": [{"offset": 0, "reason_name": "section_entry"}]}]}
    with pytest.raises(ValueError, match="no progress"):
        function_facts.analysis_function_facts("test", analysis,
            artifact_query=lambda **_: dict(items=[], has_more=True))


@pytest.mark.parametrize('generated', [True, None])
def test_generated_or_unversioned_render_name_keeps_existing_function_name(generated):
    analysis = {'sections': [{'section_index': 0, 'blocks': [], 'edges': [],
        'code_start_refs': [{'offset': 0, 'reason_name': 'section_entry'}],
        'symbol_origins': [{'offset': 0, 'symbol_name': 'original_entry'}]}]}
    row = dict(name='abs_0_00001000', provenance='typed_render_declaration',
               declaration_kind=1, section_index=0, source_offset=0,
               source_symbol=dict(section_index=0, source_offset=0))
    if generated is not None:
        row['name_is_generated'] = generated
    result = function_facts.analysis_function_facts('test', analysis,
        artifact_query=lambda **_: dict(items=[row], has_more=False))['functions'][0]
    assert result['name'] == 'original_entry'
    assert result['names'] == ['abs_0_00001000', 'original_entry']


def _forwarder_fixture(chain=False, pc_relative=False):
    starts = [0, 6, 12] if chain else [0, 6]
    blocks = [dict(start_offset=p, end_offset=p+(2 if p==starts[-1] else 6)) for p in starts]
    edges = [dict(source_block_index=i,target_block_index=i+1,source_offset=p,
                  target_offset=starts[i+1],kind=4)for i,p in enumerate(starts[:-1])]
    edges.append(dict(source_block_index=len(starts)-1,target_block_index=0xFFFFFFFF,
                      source_offset=starts[-1],target_offset=0xFFFFFFFF,kind=5))
    section = dict(section_index=0,blocks=blocks,edges=edges,
                   code_start_refs=[dict(offset=0,reason_name='section_entry')])
    instructions = {p:dict(section_index=0,source_offset=p,size=6,provenance='accepted_instruction',
        operand_facts=[dict(access='branch_target',indexed=False,
                           absolute_address=None if pc_relative else 0x1000+starts[i+1],
                           base_register=None,pc_relative=pc_relative,displacement_known=True)])
                    for i,p in enumerate(starts[:-1])}
    calls=[]
    def query(**kw):
        calls.append(kw)
        p=kw['source_offset'];kind=kw['kind']
        if kind=='instructions':rows=[instructions[p]]
        elif kind=='edges':
            assert kw['direction']=='outgoing'
            e=next(e for e in edges if e['source_offset']==p)
            rows=[dict(section_index=0,source_offset=p,target_section_index=0,
                       target_offset=e['target_offset'],kind='jump',status='resolved',provenance='native_cfg')]
        else:
            assert kind=='symbols'
            rows=[dict(name='restored_target'if p==starts[-1]else f'entry_{p}',
                provenance='typed_render_declaration',declaration_kind=1,name_is_generated=False,
                section_index=0,source_offset=p,source_symbol=dict(section_index=0,source_offset=p))]
        return dict(items=rows,has_more=False)
    return dict(sections=[section]),instructions,query,calls


@pytest.mark.parametrize('chain,pc_relative',[(False,False),(True,False),(False,True)])
def test_single_jump_entries_close_over_accepted_targets(chain,pc_relative):
    analysis,_,query,calls=_forwarder_fixture(chain,pc_relative)
    before=function_facts.analysis_function_facts('fixture',analysis)['functions']
    after=function_facts.analysis_function_facts('fixture',analysis,artifact_query=query)['functions']
    assert len(before)==1 and len(after)==(3 if chain else 2)
    assert after[0]['ranges']==[dict(start_offset=0,end_offset=6)]
    assert after[0]['forwarding_target']==dict(section_index=0,source_offset=6)
    assert not after[-1]['callers']  # A tail forwarder is not a CALL.
    assert after[-1]['incoming_forwarding_entries']==[6 if chain else 0]
    assert after[-1]['name']=='restored_target'
    assert 'forwarding_target_may_be_shared_entry'in after[-1]['unknowns']
    assert sum(c['kind']=='instructions'for c in calls)==len(after)-1
    assert {p for f in before for r in f['ranges']for p in range(r['start_offset'],r['end_offset'])}=={
        p for f in after for r in f['ranges']for p in range(r['start_offset'],r['end_offset'])}


@pytest.mark.parametrize('bad',[
    'setup_before_jump','conditional','indirect','indexed','missing_literal','wrong_source',
    'wrong_section','not_accepted','target_not_a_block','target_mismatch','stale_native_edge',
    'ambiguous_instruction','ambiguous_edge','cross_section_edge','branch_only',
])
def test_forwarder_discovery_refuses_incomplete_or_inconsistent_native_evidence(bad):
    analysis,rows,query,_=_forwarder_fixture();s=analysis['sections'][0];row=rows[0]
    if bad=='setup_before_jump':s['blocks'][0]['end_offset']=8
    elif bad=='conditional':s['edges'].append(dict(source_block_index=0,target_block_index=1,
        source_offset=0,target_offset=6,kind=1))
    elif bad=='indirect':row['operand_facts'][0].update(base_register='A0',absolute_address=None)
    elif bad=='indexed':row['operand_facts'][0]['indexed']=True
    elif bad=='missing_literal':row['operand_facts'][0]['absolute_address']=None
    elif bad=='wrong_source':row['source_offset']=2
    elif bad=='wrong_section':row['section_index']=1
    elif bad=='not_accepted':row['provenance']='candidate_instruction'
    elif bad=='target_not_a_block':s['edges'][0]['target_block_index']=0xFFFFFFFF
    elif bad=='target_mismatch':s['edges'][0]['target_offset']=7
    elif bad=='branch_only':s['edges'][0]['kind']=2
    def supplied(**kw):
        page=query(**kw)
        if bad=='stale_native_edge'and kw['kind']=='edges':page['items'][0]['target_offset']=8
        if bad=='cross_section_edge'and kw['kind']=='edges':page['items'][0]['target_section_index']=1
        if bad=='ambiguous_instruction'and kw['kind']=='instructions':page['has_more']=True
        if bad=='ambiguous_edge'and kw['kind']=='edges':page['items'].append(dict(page['items'][0]))
        return page
    after=function_facts.analysis_function_facts('fixture',analysis,artifact_query=supplied)['functions']
    assert len(after)==1 and after[0]['forwarding_target']is None


def test_named_jump_block_without_native_entry_is_not_a_function_seed():
    analysis,_,query,calls=_forwarder_fixture()
    analysis['sections'][0]['code_start_refs']=[]
    analysis['sections'][0]['symbol_origins']=[dict(offset=0,symbol_name='named_block')]
    result=function_facts.analysis_function_facts('fixture',analysis,artifact_query=query)
    assert not result['functions'] and not calls


def test_forwarder_cycle_is_finite_and_does_not_claim_a_return():
    analysis,rows,query,calls=_forwarder_fixture(chain=True);s=analysis['sections'][0]
    # The second stub returns to the original entry. The unreferenced final
    # block is accepted code, not automatically a function.
    s['edges'][1].update(target_block_index=0,target_offset=0)
    result=function_facts.analysis_function_facts('fixture',analysis,artifact_query=query)['functions']
    assert [f['source_offset']for f in result]==[0,6]
    assert result[1]['forwarding_target']['source_offset']==0
    assert all(f['status']=='candidate'for f in result)
    assert sum(c['kind']=='instructions'for c in calls)==2


@pytest.mark.parametrize('operand',['target.l','target(pc)'])
def test_forwarding_closure_uses_actual_native_instruction_and_edge_queries(tmp_path,operand):
    from tests.test_app_cursor_propagation import cursor_artifact
    a,original=cursor_artifact(tmp_path,f' jmp {operand}\ntarget:\n',regions=False,
                              metadata_extra=dict(target_type='program',entry_register_seeds=[]))
    try:
        analysis=a.analysis_payload()[0]
        result=function_facts.analysis_function_facts('fixture',analysis,
                                                     artifact_query=a.query_payload)['functions']
        assert len(result)==2
        assert result[0]['forwarding_target']==dict(section_index=0,source_offset=len(original)-2)
        assert result[1]['incoming_forwarding_entries']==[0]
        from amiga_reversing.disasm import c_backend
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',
            a.inline_source_text_with_profile()[0])[0]==original
    finally:a.close()
