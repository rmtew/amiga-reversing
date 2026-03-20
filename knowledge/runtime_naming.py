"""Generated runtime naming knowledge artifact. Do not edit directly."""

from __future__ import annotations

META = {'source': 'Parser-asserted from Amiga OS calling conventions',
 'description': 'Rules for naming subroutines from their OS call patterns'}
PATTERNS = [{'functions': ['OpenLibrary', 'AllocMem'], 'name': 'init_app'},
 {'functions': ['CloseLibrary', 'FreeMem'], 'name': 'cleanup_app'},
 {'functions': ['AllocMem'], 'name': 'alloc_memory'},
 {'functions': ['FreeMem'], 'name': 'free_memory'},
 {'functions': ['AllocMem', 'FreeMem'], 'name': 'manage_memory'},
 {'functions': ['SetSignal'], 'name': 'check_signals'},
 {'functions': ['AvailMem'], 'name': 'check_memory'},
 {'functions': ['OpenDevice'], 'name': 'open_device', 'partial': True}]
TRIVIAL_FUNCTIONS = ['AllocMem', 'FreeMem', 'SetSignal']
GENERIC_PREFIX = 'call_'
