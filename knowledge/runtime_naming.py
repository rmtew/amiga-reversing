"""Generated runtime naming knowledge artifact. Do not edit directly."""

RUNTIME = {'_meta': {'source': 'Parser-asserted from Amiga OS calling conventions',
           'description': 'Rules for naming subroutines from their OS call patterns'},
 'patterns': [{'functions': ['OpenLibrary', 'AllocMem'], 'name': 'init_app'},
              {'functions': ['CloseLibrary', 'FreeMem'], 'name': 'cleanup_app'},
              {'functions': ['AllocMem'], 'name': 'alloc_memory'},
              {'functions': ['FreeMem'], 'name': 'free_memory'},
              {'functions': ['AllocMem', 'FreeMem'], 'name': 'manage_memory'},
              {'functions': ['SetSignal'], 'name': 'check_signals'},
              {'functions': ['AvailMem'], 'name': 'check_memory'},
              {'functions': ['OpenDevice'], 'name': 'open_device', 'partial': True}],
 'trivial_functions': ['AllocMem', 'FreeMem', 'SetSignal'],
 'generic_prefix': 'call_'}
