"""Field coordinates follow generated emission order, checked against vasm."""
import json
import subprocess
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def span_probe(tmp_path_factory):
    out=tmp_path_factory.mktemp('operand-span')
    source=out/'probe.c'
    source.write_text(r'''
#include "m68k_assembler.h"
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char **argv) {
 if(argc!=2)return 1;
 M68kAsmOperandValue o[2]={{.kind=M68K_ASM_OPERAND_IMM,.value=0x10014},
   {.kind=M68K_ASM_OPERAND_EA,.ea_mode=0,.ea_reg=0}};
 const char *name="subi"; char size='l'; size_t count=2;
 switch(atoi(argv[1])) {
 case 1:name="move";o[0].kind=M68K_ASM_OPERAND_EA;o[0].ea_mode=7;o[0].ea_reg=4;
   o[1].ea_mode=7;o[1].ea_reg=1;o[1].value=0x20028;break;
 case 2:name="lea";size=0;o[0].kind=M68K_ASM_OPERAND_EA;o[0].ea_mode=7;o[0].ea_reg=1;
   o[1].kind=M68K_ASM_OPERAND_AN;break;
 case 3:name="bra";size='b';count=1;o[0].kind=M68K_ASM_OPERAND_LABEL;o[0].value=4;break;
 case 4:name="bra";size='w';count=1;o[0].kind=M68K_ASM_OPERAND_LABEL;o[0].value=4;break;
 default:break;
 }
 uint8_t id=m68k_asm_mnemonic_id_from_name(name);
 uint16_t f=m68k_asm_form_index_for_operands_id(id,o,count,size,M68K_ASM_CPU_68000),fields[64];
 if(f==M68K_ASM_FORM_NONE || m68k_asm_build_patch_values(f,size,o,count,fields,64))return 2;
 M68kAsmInstructionSpec spec={.mnemonic_id=id,.size_suffix=size,.target_cpu=M68K_ASM_CPU_68000,
  .operand_count=count,.operands=o,.patch_values=fields,.patch_value_count=g_m68k_asm_forms[f].patch_count};
 unsigned char bytes[32];size_t n;
 if(m68k_asm_assemble_instruction(&spec,bytes,32,&n))return 3;
 printf("{\"bytes\":\"");for(size_t i=0;i<n;i++)printf("%02x",bytes[i]);printf("\",\"spans\":[");
 for(size_t i=0;i<count;i++) {size_t offset,extent;
  if(m68k_asm_operand_extension_span(f,o,count,size,i,&offset,&extent))return 4;
  printf("%s[%zu,%zu]",i ? ",":"",offset,extent);
 }
 size_t offset=99,extent=99;
 if(m68k_asm_operand_extension_span(f,o,count,size,count,&offset,&extent)!=-1 || offset || extent)return 5;
 puts("]}");return 0;
}
''')
    executable=out/'probe'
    subprocess.run(['cc','-Isrc',str(source),'-Lsrc/build','-lamiga_backend',
        f'-Wl,-rpath,{ROOT}/src/build','-o',str(executable)],cwd=ROOT,check=True,capture_output=True)
    return executable


@pytest.mark.parametrize('case,instruction,spans',[
    (0,'subi.l #$10014,d0',[[2,4],[0,0]]),
    (1,'move.l #$10014,$20028.l',[[2,4],[6,4]]),
    (2,'lea $10014.l,a0',[[2,4],[0,0]]),
    (3,'bra.b *+6',[[0,0]]),
    (4,'bra.w *+6',[[2,2]]),
])
def test_generated_spans_and_full_instruction_match_vasm(span_probe,tmp_path,case,instruction,spans):
    result=json.loads(subprocess.check_output([str(span_probe),str(case)],text=True))
    source=tmp_path/'oracle.s';source.write_text(' org 0\n '+instruction+'\n')
    binary=tmp_path/'oracle.bin'
    subprocess.run([str(ROOT/'tools/vasmm68k_mot.exe'),'-quiet','-Fbin','-m68000','-no-opt',
        '-o',str(binary),str(source)],check=True,capture_output=True)
    assert result['spans']==spans
    assert bytes.fromhex(result['bytes'])==binary.read_bytes()
