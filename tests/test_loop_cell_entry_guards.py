"""Late entry changes retract sparse loop-exit facts without cached values."""
import os
import shutil
import subprocess
from pathlib import Path
import pytest


def test_loop_cell_guards_use_current_entries_and_strip_stale_predicates(tmp_path):
    root=Path(__file__).resolve().parents[1]
    cc=shutil.which('cc')
    backend=Path(os.environ.get('AMIGA_TEST_BACKEND',root/'src/build/libamiga_backend.so'))
    if not cc or not backend.exists():
        pytest.skip('native compiler and backend required')
    source=tmp_path/'loop-entry.c'
    source.write_text(r'''#include "m68k_analysis_render_lookup.c"
#include <assert.h>
int main(void) {
 M68kRenderTypedFlowNode nodes[5]={0}; M68kRenderTypedStorageSlot storage={0};
 M68kRenderTypedFlowGraph graph={0}; M68kRenderLookup lookup={0};
 M68kLoopCellSummary summary={0}; M68kLoopEntryRoot root={0};
 M68kRenderTypedStoredValue value={0}; M68kRenderTypedState out={0};
 size_t entries[]={0,4},body[]={1,2}; uint32_t ids[]={1};
 storage.kind=M68K_RENDER_TYPED_STORAGE_ABSOLUTE;storage.address=0x3000;
 lookup.typed_storage_slots=&storage;lookup.typed_storage_slot_count=1;
 graph.nodes=nodes;graph.node_count=5;graph.loop_cells=&summary;graph.loop_cell_count=1;
 summary.tail=2;summary.exit=3;summary.counter=2;summary.iterations=8;
 summary.entries=entries;summary.entry_count=1;summary.body=body;summary.body_count=2;
 summary.storage_ids=ids;summary.storage_count=1;summary.requirements=&root;summary.requirement_count=1;
 root.kind=M68K_LOOP_ROOT_ADDRESS;root.reg=1;root.address=1;root.raw_count=1;root.raw_values[0]=0x68000;
 nodes[0].has_out=1;nodes[0].platform_out.word_values[2].count=1;
 nodes[0].platform_out.word_values[2].values[0]=7;
 nodes[0].typed_out.addr_regs[1].known=nodes[0].typed_out.addr_regs[1].raw_long_value_known=1;
 nodes[0].typed_out.addr_regs[1].raw_long_value=0x68000;
 typed_stored_value_set_raw_long(&value,0x60000);value.read_relation=13;
 typed_state_set_memory_cell(&nodes[0].typed_out,1,&value);
 typed_flow_refine_loop_cell_edge(&graph,&lookup,2,3,&out);
 assert(typed_state_memory_cell(&out,1)->value.raw_long_value==0x60000);
 assert(!typed_state_memory_cell(&out,1)->value.read_relation);
 /* A new entry value supplies the packet; the original value was not cached. */
 typed_stored_value_set_raw_long(&value,0x61000);value.read_relation=0;
 typed_state_set_memory_cell(&nodes[0].typed_out,1,&value);typed_state_clear_all(&out);
 typed_flow_refine_loop_cell_edge(&graph,&lookup,2,3,&out);
 assert(typed_state_memory_cell(&out,1)->value.raw_long_value==0x61000);
 /* A late widened or unknown address/count cannot borrow the earlier proof. */
 nodes[0].typed_out.addr_regs[1].raw_long_value=0x3000;typed_state_clear_all(&out);
 typed_flow_refine_loop_cell_edge(&graph,&lookup,2,3,&out);assert(!out.base_slot_count);
 nodes[0].typed_out.addr_regs[1].raw_long_value=0x68000;
 nodes[0].platform_out.word_values[2].count=2;typed_state_clear_all(&out);
 typed_flow_refine_loop_cell_edge(&graph,&lookup,2,3,&out);assert(!out.base_slot_count);
 nodes[0].platform_out.word_values[2].count=1;
 nodes[1].is_root=1;typed_flow_refine_loop_cell_edge(&graph,&lookup,2,3,&out);assert(!out.base_slot_count);
 nodes[1].is_root=0;
 /* All real entries must carry the cell. Incompatible joins do not revive it. */
 nodes[4]=nodes[0];nodes[4].typed_out.base_slot_count=0;summary.entry_count=2;
 typed_flow_refine_loop_cell_edge(&graph,&lookup,2,3,&out);assert(!out.base_slot_count);
 assert(!typed_flow_index_loop_cell_dependencies(&graph));
 assert(graph.loop_cell_dependency_count==2 && graph.loop_cell_dependencies[1].entry==4);
 assert(typed_flow_loop_cell_dependency_start(&graph,4)==1);
 free(graph.loop_cell_dependencies);
 /* Canonical producer disappearance is INVALID for a table-derived packet,
  * never an independent type contract that survives the next epoch. */
 M68kSourceAnalysisIR analysis={0};M68kSectionAnalysisIR section={0};M68kAddressValueIR producer={0};
 M68kRenderTypedProvenance provenance=typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_STATIC_DATA,0,0x20);
 analysis.sections=&section;analysis.section_count=1;section.address_values=&producer;section.address_value_count=1;
 producer.origin_kind=M68K_PLATFORM_TYPE_PROVENANCE_STATIC_DATA;producer.producer_offset=0x20;
 producer.table_origin.has_origin=1;producer.table_origin.selection_kind=M68K_ADDRESS_VALUE_TABLE_SELECTION_SINGLETON;
 producer.table_origin.entry_index=0;producer.table_origin.terminal_kind=M68K_ADDRESS_VALUE_TERMINAL_RESOLVED;
 producer.terminal_kind=M68K_ADDRESS_VALUE_TERMINAL_RESOLVED;
 producer.resolution=M68K_ADDRESS_VALUE_RESOLUTION_RESOLVED;producer.has_target=1;
 producer.candidate_target_count=1;producer.render_outcome=M68K_ADDRESS_VALUE_RENDER_NON_SOURCE;
 M68kAddressValueTableOriginIR origin=producer.table_origin;
 assert(source_analysis_table_contract_state(&analysis,&provenance,&origin,NULL)==M68K_RENDER_TABLE_CONTRACT_VALID);
 section.address_value_count=0;
 assert(source_analysis_table_contract_state(&analysis,&provenance,&origin,NULL)==M68K_RENDER_TABLE_CONTRACT_INVALID);
 origin.has_origin=0;
 assert(source_analysis_table_contract_state(&analysis,&provenance,&origin,NULL)==M68K_RENDER_TABLE_CONTRACT_NOT_TABLE_DERIVED);
 /* Shared roots survive numeric imprecision, independent of join order. */
 M68kRenderTypedRegValue precise={0},symbolic={0},joined={0};
 precise.known=symbolic.known=1;precise.layout_base_id=symbolic.layout_base_id=1;
 precise.raw_long_value_known=1;precise.raw_long_value=0x60000;
 joined=precise;typed_reg_merge(&joined,&symbolic,NULL);
 assert(joined.known && joined.layout_base_id==1 && !joined.raw_long_value_known && !joined.type_conflicted);
 symbolic=joined;joined=precise;typed_reg_merge(&symbolic,&joined,NULL);
 assert(symbolic.known && symbolic.layout_base_id==1 && !symbolic.raw_long_value_known && !symbolic.type_conflicted);
 joined=symbolic;assert(!typed_reg_merge(&joined,&symbolic,NULL));
 precise.layout_base_id=2;typed_reg_merge(&joined,&precise,NULL);assert(!joined.layout_base_id);
 memset(&precise,0,sizeof(precise));typed_reg_merge(&symbolic,&precise,NULL);
 assert(!symbolic.known && !symbolic.layout_base_id);
 return 0;
}''')
    exe=tmp_path/'loop-entry'
    built=subprocess.run([cc,'-Isrc','-D_POSIX_C_SOURCE=200809L','-std=c11','-O0',str(source),str(backend),
        f'-Wl,-rpath,{backend.parent}','-lm','-o',str(exe)],cwd=root,capture_output=True,text=True,timeout=60)
    assert built.returncode==0,built.stderr
    run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
    assert run.returncode==0,run.stdout+run.stderr
