import json
import sys
from types import ModuleType, SimpleNamespace

import pytest

from amiga_reversing.disasm.behaviour_validation import OUTCOMES
from amiga_reversing.tools import restoration, restoration_mcp


@pytest.mark.parametrize('status',sorted(OUTCOMES))
def test_cli_nonpass_receipt_never_has_success_exit(monkeypatch,tmp_path,capsys,status):
    seen=[]
    def call(target,operation,**parameters):
        seen.append((target,operation,parameters));return dict(status=status)
    monkeypatch.setattr(restoration,'RestorationClient',lambda *args:SimpleNamespace(call=call))
    request=tmp_path/'request.json';request.write_text(json.dumps(dict(
        expected_revision='inspected',contract_id='canonical',capture='.runtime-state/evidence.json')))
    code=restoration.main(['--target','target','behaviour','--request',str(request)])
    assert code==(0 if status=='pass' else 2)
    assert json.loads(capsys.readouterr().out)['status']==status
    assert seen[0][1]=='behaviour' and seen[0][2]['expected_revision']=='inspected'


def test_mcp_registration_forwards_to_the_same_service_without_sdk(monkeypatch):
    # Unit-check the thin adapter even where the optional SDK/stdio test skips.
    # This is not evidence of an installed or live MCP transport.
    class Server:
        def __init__(self,*args,**kwargs):self.functions={}
        def tool(self,**kwargs):
            def register(fn):self.functions[fn.__name__]=fn;return fn
            return register
    for name in ['mcp','mcp.server','mcp.server.mcpserver','mcp.server.mcpserver.exceptions','mcp.types']:
        module=ModuleType(name);module.__path__=[];monkeypatch.setitem(sys.modules,name,module)
    monkeypatch.setattr(sys.modules['mcp.server'],'MCPServer',Server,raising=False)
    monkeypatch.setattr(sys.modules['mcp.server.mcpserver.exceptions'],'ToolError',RuntimeError,raising=False)
    monkeypatch.setattr(sys.modules['mcp.types'],'ToolAnnotations',SimpleNamespace,raising=False)
    calls=[]
    def call(*args,**kwargs):calls.append((args,kwargs));return dict(status='incomplete_truncated')
    server=restoration_mcp.create_server(SimpleNamespace(call=call))
    result=server.functions['restoration_behaviour']('target','inspected','canonical',capture='.runtime-state/evidence.json')
    assert result['status']=='incomplete_truncated'
    assert calls==[(('target','behaviour'),dict(expected_revision='inspected',contract_id='canonical',
                  manifest=None,capture='.runtime-state/evidence.json',previous_receipt_id=None))]
