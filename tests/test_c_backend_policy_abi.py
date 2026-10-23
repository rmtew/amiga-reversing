"""The direct-native test mirror must allocate the current complete policy."""
import ctypes
from pathlib import Path
import shutil
import subprocess

import pytest

from tests.test_c_backend import _M68kAnalysisPolicy


def test_policy_ctypes_fields_match_native_header_before_native_writes(tmp_path):
    compiler=shutil.which('cc')
    if not compiler:pytest.skip('C header ABI probe requires the local cc compiler')
    source=tmp_path/'policy-abi.c';binary=tmp_path/'policy-abi'
    statements=['#include <stdio.h>','#include <stddef.h>','#include "m68k_ir.h"','int main(void){']
    for name,_ in _M68kAnalysisPolicy._fields_:
        statements.append(f'printf("{name} %zu %zu\\n",offsetof(M68kAnalysisPolicy,{name}),sizeof(((M68kAnalysisPolicy*)0)->{name}));')
    statements.append('}')
    source.write_text('\n'.join(statements))
    root=Path(__file__).resolve().parents[1]
    subprocess.run([compiler,'-I',str(root/'src'),'-o',str(binary),str(source)],check=True,capture_output=True)
    for row in subprocess.check_output([str(binary)]).decode().splitlines():
        name,offset,size=row.split();field=getattr(_M68kAnalysisPolicy,name)
        assert (field.offset,field.size)==(int(offset),int(size)),name
