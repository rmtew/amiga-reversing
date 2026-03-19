"""Generated runtime hunk knowledge artifact. Do not edit directly."""

RUNTIME = {'_meta': {'sources': [{'file': 'D:/NDK/NDK_3.1/INCLUDES&LIBS/INCLUDE_H/DOS/DOSHUNKS.H',
                        'type': 'official',
                        'description': 'NDK 3.1 DOSHUNKS.H — Amiga Inc. hunk type definitions, ext '
                                       'sub-types, memory flags',
                        'version': '$VER: doshunks.h 36.9',
                        'provides': ['hunk_types',
                                     'ext_types',
                                     'memory_flags',
                                     'compatibility_notes']},
                       {'file': 'NDK_3.1/EXAMPLES1/PCMCIA/AMIGAXIP/LOADSEG.ASM',
                        'type': 'official',
                        'description': 'NDK 3.1 reference LoadSeg implementation — defines wire '
                                       'format for all hunk types through executable code (not '
                                       'prose)',
                        'provides': ['reloc_formats',
                                     'hunk_content_formats',
                                     'load_file_valid_types'],
                        'note': 'Wire format entries are parser-asserted from the reference '
                                'implementation with line citations'}],
           'note': 'Parsed from NDK 3.1 by parse_hunk_format.py',
           'longword_bytes': 4,
           'endianness': 'big',
           'hunk_type_id_mask': 536870911,
           'size_longs_mask': 1073741823,
           'mem_flags_shift': 30,
           'ext_type_and_len_packing': {'type_bits': [31, 24],
                                        'type_width': 8,
                                        'name_len_bits': [23, 0],
                                        'name_len_width': 24,
                                        'citation': 'amiga_hunk_format.md line 138: bits 31-24 = '
                                                    'sub-type, bits 23-0 = name_len (in '
                                                    'longwords)'},
           'load_file_citation': 'LOADSEG.ASM lines 163-180: switch table has 15 entries '
                                 '(HUNK_NAME through HUNK_BREAK). Note: '
                                 'RELOC16/RELOC8/EXT/HEADER/OVERLAY/BREAK all fall through to '
                                 'lssFail (line 290-298), meaning they are recognized but '
                                 'rejected.'},
 'hunk_types': {'HUNK_UNIT': {'id': 999, 'description': '', 'notes': 'hunk types'},
                'HUNK_NAME': {'id': 1000, 'description': ''},
                'HUNK_CODE': {'id': 1001, 'description': ''},
                'HUNK_DATA': {'id': 1002, 'description': ''},
                'HUNK_BSS': {'id': 1003, 'description': ''},
                'HUNK_RELOC32': {'id': 1004, 'description': ''},
                'HUNK_ABSRELOC32': {'description': '', 'alias_of': 'HUNK_RELOC32'},
                'HUNK_RELOC16': {'id': 1005, 'description': ''},
                'HUNK_RELRELOC16': {'description': '', 'alias_of': 'HUNK_RELOC16'},
                'HUNK_RELOC8': {'id': 1006, 'description': ''},
                'HUNK_RELRELOC8': {'description': '', 'alias_of': 'HUNK_RELOC8'},
                'HUNK_EXT': {'id': 1007, 'description': ''},
                'HUNK_SYMBOL': {'id': 1008, 'description': ''},
                'HUNK_DEBUG': {'id': 1009, 'description': ''},
                'HUNK_END': {'id': 1010, 'description': ''},
                'HUNK_HEADER': {'id': 1011, 'description': ''},
                'HUNK_OVERLAY': {'id': 1013, 'description': ''},
                'HUNK_BREAK': {'id': 1014, 'description': ''},
                'HUNK_DREL32': {'id': 1015, 'description': ''},
                'HUNK_DREL16': {'id': 1016, 'description': ''},
                'HUNK_DREL8': {'id': 1017, 'description': ''},
                'HUNK_LIB': {'id': 1018, 'description': ''},
                'HUNK_INDEX': {'id': 1019, 'description': ''},
                'HUNK_RELOC32SHORT': {'id': 1020,
                                      'description': '',
                                      'notes': 'Note: V37 LoadSeg uses 1015 (HUNK_DREL32) by '
                                               'mistake.  This will continue to be supported in '
                                               'future versions, since HUNK_DREL32 is illegal in '
                                               'load files anyways.  Future versions will support '
                                               'both 1015 and 1020, though anything that should be '
                                               'usable under V37 should use 1015.'},
                'HUNK_RELRELOC32': {'id': 1021,
                                    'description': '',
                                    'notes': 'see ext_xxx below.  New for V39 (note that LoadSeg '
                                             'only handles RELRELOC32).'},
                'HUNK_ABSRELOC16': {'id': 1022, 'description': ''}},
 'ext_types': {'EXT_SYMB': {'id': 0, 'description': 'symbol table'},
               'EXT_DEF': {'id': 1, 'description': 'relocatable definition'},
               'EXT_ABS': {'id': 2, 'description': 'Absolute definition'},
               'EXT_RES': {'id': 3, 'description': 'no longer supported'},
               'EXT_REF32': {'id': 129, 'description': '32 bit absolute reference to symbol'},
               'EXT_ABSREF32': {'description': '', 'alias_of': 'EXT_REF32'},
               'EXT_COMMON': {'id': 130,
                              'description': '32 bit absolute reference to COMMON block',
                              'has_common_size': True},
               'EXT_ABSCOMMON': {'description': '', 'alias_of': 'EXT_COMMON'},
               'EXT_REF16': {'id': 131, 'description': '16 bit PC-relative reference to symbol'},
               'EXT_RELREF16': {'description': '', 'alias_of': 'EXT_REF16'},
               'EXT_REF8': {'id': 132, 'description': '8 bit PC-relative reference to symbol'},
               'EXT_RELREF8': {'description': '', 'alias_of': 'EXT_REF8'},
               'EXT_DEXT32': {'id': 133, 'description': '32 bit data relative reference'},
               'EXT_DEXT16': {'id': 134, 'description': '16 bit data relative reference'},
               'EXT_DEXT8': {'id': 135, 'description': '8 bit data relative reference'},
               'EXT_RELREF32': {'id': 136, 'description': '32 bit PC-relative reference to symbol'},
               'EXT_RELCOMMON': {'id': 137,
                                 'description': '32 bit PC-relative reference to COMMON block',
                                 'has_common_size': True},
               'EXT_ABSREF16': {'id': 138, 'description': '16 bit absolute reference to symbol'},
               'EXT_ABSREF8': {'id': 139, 'description': '8 bit absolute reference to symbol'}},
 'memory_flags': {'HUNKB_ADVISORY': {'bit': 29, 'description': ''},
                  'HUNKB_CHIP': {'bit': 30, 'description': ''},
                  'HUNKB_FAST': {'bit': 31, 'description': ''}},
 'memory_type_codes': {'0': {'name': 'ANY', 'description': 'Any available memory'},
                       '1': {'name': 'CHIP', 'description': 'Chip RAM (MEMF_CHIP)'},
                       '2': {'name': 'FAST', 'description': 'Fast RAM (MEMF_FAST)'},
                       '3': {'name': 'EXTENDED',
                             'description': 'Extended: next ULONG has exec memory attrs'}},
 'ext_type_categories': {'definition_range': [0, 3],
                         'reference_range': [129, 139],
                         'boundary': 128,
                         'citation': 'DOSHUNKS.H: definitions 0-3, references 129-139; boundary at '
                                     '128 (bit 7)'},
 'compatibility_notes': [{'topic': 'HUNK_DREL32_as_RELOC32SHORT',
                          'text': 'Note: V37 LoadSeg uses 1015 (HUNK_DREL32) by mistake.  This '
                                  'will continue to be supported in future versions, since '
                                  'HUNK_DREL32 is illegal in load files anyways.  Future versions '
                                  'will support both 1015 and 1020, though anything that should be '
                                  'usable under V37 should use 1015.',
                          'applies_to': ['HUNK_RELOC32SHORT']}],
 'reloc_formats': {'long': {'description': 'Standard 32-bit reloc format',
                            'fields': [{'name': 'count',
                                        'type': 'ULONG',
                                        'note': 'Number of offsets; 0 = terminator'},
                                       {'name': 'target_hunk',
                                        'type': 'ULONG',
                                        'note': 'Hunk index to add base of'},
                                       {'name': 'offsets',
                                        'type': 'ULONG[]',
                                        'note': 'count × reloc offsets within current hunk'}],
                            'terminator': 'count == 0',
                            'applies_to': ['HUNK_RELOC32',
                                           'HUNK_RELOC16',
                                           'HUNK_RELOC8',
                                           'HUNK_DREL32',
                                           'HUNK_DREL16',
                                           'HUNK_DREL8',
                                           'HUNK_RELRELOC32',
                                           'HUNK_ABSRELOC16'],
                            'citation': 'LOADSEG.ASM lines 238-261: lssHunkReloc32 uses GetLong '
                                        '(ULONG) for count, target, and each offset'},
                   'short': {'description': 'Compact 16-bit reloc format',
                             'fields': [{'name': 'count',
                                         'type': 'UWORD',
                                         'note': 'Number of offsets; 0 = terminator'},
                                        {'name': 'target_hunk', 'type': 'UWORD'},
                                        {'name': 'offsets',
                                         'type': 'UWORD[]',
                                         'note': 'count × reloc offsets (16-bit, max 64K)'}],
                             'terminator': 'count == 0, then align to longword boundary',
                             'applies_to': ['HUNK_RELOC32SHORT'],
                             'citation': 'DOSHUNKS.H lines 42-47: V37 LoadSeg uses HUNK_DREL32 '
                                         '(1015) for this format in load files. HUNK_DREL32 is '
                                         'illegal in load files, so 1015 unambiguously means short '
                                         'relocs in executables.'}},
 'relocation_semantics': {'HUNK_RELOC32': {'bytes': 4,
                                           'mode': 'absolute',
                                           'description': 'Add target hunk base to 32-bit value at '
                                                          'offset',
                                           'citation': 'LOADSEG.ASM line 256; DOSHUNKS.H '
                                                       'HUNK_ABSRELOC32 alias'},
                          'HUNK_RELOC32SHORT': {'bytes': 4,
                                                'mode': 'absolute',
                                                'description': 'Same as RELOC32, compact encoding'},
                          'HUNK_RELOC16': {'bytes': 2,
                                           'mode': 'pc_relative',
                                           'description': '16-bit PC-relative displacement',
                                           'citation': 'DOSHUNKS.H HUNK_RELRELOC16 alias'},
                          'HUNK_RELOC8': {'bytes': 1,
                                          'mode': 'pc_relative',
                                          'description': '8-bit PC-relative displacement',
                                          'citation': 'DOSHUNKS.H HUNK_RELRELOC8 alias'},
                          'HUNK_DREL32': {'bytes': 4,
                                          'mode': 'data_relative',
                                          'description': '32-bit data-section-relative offset'},
                          'HUNK_DREL16': {'bytes': 2,
                                          'mode': 'data_relative',
                                          'description': '16-bit data-section-relative offset'},
                          'HUNK_DREL8': {'bytes': 1,
                                         'mode': 'data_relative',
                                         'description': '8-bit data-section-relative offset'},
                          'HUNK_RELRELOC32': {'bytes': 4,
                                              'mode': 'pc_relative',
                                              'description': '32-bit PC-relative displacement '
                                                             '(V39+)',
                                              'citation': 'DOSHUNKS.H: New for V39'},
                          'HUNK_ABSRELOC16': {'bytes': 2,
                                              'mode': 'absolute',
                                              'description': '16-bit absolute address',
                                              'citation': 'DOSHUNKS.H'}},
 'hunk_content_formats': {'HUNK_HEADER': {'fields': [{'name': 'resident_libs',
                                                      'type': 'ULONG[]',
                                                      'note': 'Sequence of BSTRs terminated by 0; '
                                                              'LoadSeg fails if any present'},
                                                     {'name': 'table_size', 'type': 'ULONG'},
                                                     {'name': 'first_hunk', 'type': 'ULONG'},
                                                     {'name': 'last_hunk', 'type': 'ULONG'},
                                                     {'name': 'hunk_sizes',
                                                      'type': 'ULONG[]',
                                                      'note': '(last-first+1) entries; bits 30-31 '
                                                              '= CHIP/FAST memory flags'}],
                                          'citation': 'LOADSEG.ASM lines 82-107'},
                          'HUNK_CODE': {'fields': [{'name': 'size_longs',
                                                    'type': 'ULONG',
                                                    'note': 'Size in longwords; bits 30-31 = '
                                                            'memory flags'},
                                                   {'name': 'data',
                                                    'type': 'UBYTE[]',
                                                    'note': 'size_longs × 4 bytes of code'}],
                                        'citation': 'LOADSEG.ASM lines 188-210: '
                                                    'lssHunkCode/lssHunkData share the same '
                                                    'handler — read size, then data'},
                          'HUNK_DATA': {'fields': [{'name': 'size_longs', 'type': 'ULONG'},
                                                   {'name': 'data', 'type': 'UBYTE[]'}],
                                        'citation': 'Same handler as HUNK_CODE (LOADSEG.ASM line '
                                                    '189)'},
                          'HUNK_BSS': {'fields': [{'name': 'size_longs',
                                                   'type': 'ULONG',
                                                   'note': 'Size to zero-fill; no data follows'}],
                                       'citation': 'LOADSEG.ASM lines 213-235'},
                          'HUNK_SYMBOL': {'fields': [{'name': 'name_longs',
                                                      'type': 'ULONG',
                                                      'note': 'Length of name in longs; 0 = '
                                                              'terminator'},
                                                     {'name': 'name',
                                                      'type': 'UBYTE[]',
                                                      'note': 'name_longs × 4 bytes'},
                                                     {'name': 'value', 'type': 'ULONG'}],
                                          'citation': 'LOADSEG.ASM lines 264-271: ReadName + '
                                                      'GetLong loop'},
                          'HUNK_DEBUG': {'fields': [{'name': 'size_longs', 'type': 'ULONG'},
                                                    {'name': 'data',
                                                     'type': 'UBYTE[]',
                                                     'note': 'Opaque debug data, size_longs × 4 '
                                                             'bytes'}],
                                         'sub_formats': {'LINE': {'magic': 1279872581,
                                                                  'magic_text': 'LINE',
                                                                  'fields': [{'name': 'magic',
                                                                              'type': 'ULONG',
                                                                              'value': '0x4C494E45'},
                                                                             {'name': 'filename',
                                                                              'type': 'BSTR',
                                                                              'note': 'Source '
                                                                                      'filename '
                                                                                      '(ULONG len '
                                                                                      '+ len*4 '
                                                                                      'bytes)'},
                                                                             {'name': 'entries',
                                                                              'type': 'ARRAY',
                                                                              'element': [{'name': 'line',
                                                                                           'type': 'ULONG'},
                                                                                          {'name': 'offset',
                                                                                           'type': 'ULONG',
                                                                                           'note': 'SRD '
                                                                                                   '(start '
                                                                                                   'of '
                                                                                                   'routine '
                                                                                                   'data) '
                                                                                                   'offset'}]}],
                                                                  'citation': 'amiga_hunk_format.md '
                                                                              'line 175; used by '
                                                                              'vasm and DevPac '
                                                                              'GenAm for '
                                                                              'source-level '
                                                                              'debug'}},
                                         'citation': 'LOADSEG.ASM lines 274-282: GetLong loop to '
                                                     'skip'},
                          'HUNK_EXT': {'fields': [{'name': 'type_and_len',
                                                   'type': 'ULONG',
                                                   'note': 'Bits 31-24 = ext sub-type, bits 23-0 = '
                                                           'name_len (in longwords). 0 = '
                                                           'terminator.'},
                                                  {'name': 'name',
                                                   'type': 'UBYTE[]',
                                                   'note': 'name_len × 4 bytes, NUL-padded'}],
                                       'definition_fields': [{'name': 'value', 'type': 'ULONG'}],
                                       'reference_fields': [{'name': 'ref_count', 'type': 'ULONG'},
                                                            {'name': 'offsets',
                                                             'type': 'ULONG[]',
                                                             'note': 'ref_count × offsets within '
                                                                     'current hunk'}],
                                       'common_fields': [{'name': 'common_size',
                                                          'type': 'ULONG',
                                                          'note': 'Size of common block in bytes'},
                                                         {'name': 'ref_count', 'type': 'ULONG'},
                                                         {'name': 'offsets', 'type': 'ULONG[]'}],
                                       'citation': 'amiga_hunk_format.md lines 133-165; DOSHUNKS.H '
                                                   'ext sub-type definitions'},
                          'HUNK_END': {'fields': [],
                                       'citation': 'LOADSEG.ASM lines 285-287: sets limit flag, '
                                                   'returns'}},
 'load_file_valid_types': ['HUNK_NAME',
                           'HUNK_CODE',
                           'HUNK_DATA',
                           'HUNK_BSS',
                           'HUNK_RELOC32',
                           'HUNK_RELOC16',
                           'HUNK_RELOC8',
                           'HUNK_EXT',
                           'HUNK_SYMBOL',
                           'HUNK_DEBUG',
                           'HUNK_END',
                           'HUNK_HEADER',
                           'HUNK_OVERLAY',
                           'HUNK_BREAK']}
