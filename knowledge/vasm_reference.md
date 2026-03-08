# vasm M68K Reference (Motorola Syntax, Hunk Output)

Version: vasm 2.0e, M68K backend 2.8, Motorola syntax 3.19d

## Command Line

```
vasmm68k_mot [options] sourcefile
```

### Essential Options
| Option | Description |
|--------|-------------|
| `-Fhunk` | Amiga relocatable object output |
| `-Fhunkexe` | Amiga executable output (no linker needed) |
| `-o <file>` | Output filename (default: a.out) |
| `-quiet` | Suppress banner and statistics |
| `-x` | Error on undefined symbols (default: treat as external) |
| `-nosym` | Strip local symbols |
| `-I<path>` | Add include search path |
| `-D<name>[=<val>]` | Define symbol |
| `-L <file>` | Generate listing file |
| `-linedebug` | SAS/C-compatible LINE DEBUG hunk |
| `-kick1hunks` | Kickstart 1.x compatible hunks only |
| `-nocase` | Case-insensitive symbols |

### CPU Selection
| Option | CPU |
|--------|-----|
| `-m68000` | MC68000 (default, Amiga 500/1000/2000) |
| `-m68010` | MC68010 |
| `-m68020` | MC68020 (Amiga 2000+) |
| `-m68030` | MC68030 (Amiga 3000) |
| `-m68040` | MC68040 (Amiga 4000) |
| `-m68060` | MC68060 |
| `-m68020up` | 68020-68060 compatible |
| `-m68881` / `-m68882` | FPU coprocessor |
| `-m68851` | MMU coprocessor |

### Compatibility Modes
| Option | Effect |
|--------|--------|
| `-devpac` | Devpac 2.x compat (no opts, natural align, dots in ids) |
| `-phxass` | PhxAss compat (escapes, case-insensitive macros, spaces in operands) |
| `-gas` | GNU-as compat (mov/movm/jra mnemonics, pipe comments) |

### Optimization Options
| Option | Effect | Side Effects |
|--------|--------|-------------|
| `-no-opt` | Disable all | — |
| `-opt-allbra` | Optimize all branches (even with size ext) | — |
| `-opt-clr` | MOVE #0 → CLR | Read-modify-write on 68000 |
| `-opt-div` | Div by power-of-2 → shift | — |
| `-opt-lsl` | LSL #1 → ADD | Modifies V-flag |
| `-opt-movem` | MOVEM with 1-2 regs → MOVE | — |
| `-opt-mul` | Mul by power-of-2 → shift | — |
| `-opt-pea` | MOVE #x,-(SP) → PEA | Flags unmodified |
| `-opt-st` | MOVE.B #-1 → ST | Flags unmodified |
| `-opt-size` | Prefer smaller code | — |
| `-opt-speed` | Prefer faster code | — |

### Hunk Output Options
| Option | Effect |
|--------|--------|
| `-hunkpad=<code>` | Code section padding (default: 0x4e71/NOP) |
| `-keepempty` | Don't delete empty sections |
| `-databss` | Shorten sections by removing trailing zeros (hunkexe, OS 2.0+) |

## Syntax

### Labels
- Column 1 or terminated with `:`
- Double colon `::` exports (same as `xdef`)
- Local labels: `.prefix` or `$suffix`
- Local scope: between two global labels

### Numbers
| Format | Syntax | Example |
|--------|--------|---------|
| Hex | `$digits` | `$DFF180` |
| Binary | `%digits` | `%11001010` |
| Octal | `@@digits` | `@@377` |
| Decimal | digits | `1234` |

### Comments
- `;` anywhere on line
- `*` at column 1
- After operand field (whitespace-separated, unless `-spaces`)

### Strings
- Single `'text'` or double `"text"` quotes
- C-style escapes with `-esc` flag (`\n`, `\t`, `\x00`, etc.)

## Directives

### Data Definition
| Directive | Description |
|-----------|-------------|
| `dc.b/w/l/q` | Define byte/word/long/quad |
| `dc.s/d/x/p` | Define float (single/double/extended/packed) |
| `dcb.b/w/l <n>[,<fill>]` | Block of n items (default fill: 0) |
| `ds.b/w/l <n>` | Reserve space (zero-filled) |
| `dr.b/w/l <exp>` | Store PC-relative offset |
| `blk.b/w/l <n>[,<fill>]` | Devpac alias for dcb |

### Sections
| Directive | Description |
|-----------|-------------|
| `section <name>,<type>[,<mem>]` | Define section |
| `code` / `text` | Shorthand for code section |
| `data` | Shorthand for data section |
| `bss` | Shorthand for BSS section |
| `code_c` / `data_c` / `bss_c` | Chip RAM sections |
| `code_f` / `data_f` / `bss_f` | Fast RAM sections |

Type: `code`, `text`, `data`, `bss`
Memory: `chip`, `fast`

### Alignment
| Directive | Description |
|-----------|-------------|
| `even` | Align to word boundary |
| `odd` | Align to odd address |
| `cnop <off>,<align>` | Align then add offset |
| `align <bits>` | Align to 2^bits boundary |

### Symbols
| Directive | Description |
|-----------|-------------|
| `<sym> equ <exp>` | Constant (can't redefine) |
| `<sym> = <exp>` | Same as equ |
| `<sym> set <exp>` | Reassignable symbol |
| `<sym> equr <Rn>` | Register alias |
| `<sym> reg <list>` | Register list (e.g., `d0-d7/a0-a6`) |
| `xdef <sym>` | Export symbol |
| `xref <sym>` | Import external symbol |
| `public <sym>` | Export or import |
| `weak <sym>` | Weak symbol |

### Structure Offsets
| Directive | Description |
|-----------|-------------|
| `offset [<exp>]` | Start offset section (structure defs) |
| `<lab> so.<sz> <exp>` | Structure offset (increments `__SO`) |
| `clrso` / `setso <exp>` | Reset/set `__SO` |
| `<lab> rs.<sz> <exp>` | Register structure offset (`__RS`) |
| `rsset <exp>` / `rsreset` | Set/reset `__RS` |
| `<lab> fo.<sz> <exp>` | Frame offset (decrements `__FO`) |
| `cargs [#<off>,]<sym>...` | Auto-assign stack argument offsets |

### Conditional Assembly
| Directive | Description |
|-----------|-------------|
| `if <exp>` / `else` / `endif` | Basic conditional |
| `ifeq/ifne/ifgt/ifge/iflt/ifle` | Numeric comparisons |
| `ifd/ifnd <sym>` | Symbol defined/undefined |
| `ifc/ifnc <s1>,<s2>` | String compare |
| `ifb/ifnb <op>` | Blank/non-blank operand |
| `elif <exp>` | Else-if (avoids nesting) |

### Macros
```
name    macro
        ; body uses \1..\9 for args
        ; \0 = qualifier, \# = NARG
        ; \@@ = unique id
        endm
```
- 9 args default, 35 with `-allmp`/`-devpac`/`-phxass`
- `mexit` — early return
- `NARG` — argument count symbol
- `CARG` — current argument index
- Max recursion: 1000 (configurable)

### Repetition
```
        rept <count>
        ; body, REPTN = iteration (0-based)
        endr
```

### Includes
| Directive | Description |
|-----------|-------------|
| `include <file>` | Include source |
| `incbin <file>[,off[,len]]` | Include binary data |
| `incdir <path>` | Add include search path |

### Other
| Directive | Description |
|-----------|-------------|
| `org <exp>` | Set absolute origin |
| `end` | Stop assembly |
| `fail <msg>` | Force error |
| `assert <exp>` | Error if false |
| `printt <str>` | Print string |
| `printv <exp>` | Print value |
| `rem` / `erem` | Block comment |
| `inline` / `einline` | Isolated local label scope |
| `near [<An>]` / `far` | Small data mode on/off |
| `basereg <exp>,<An>` / `endb` | Base-relative addressing block |

## Operator Precedence (high to low)
1. `+ - ! ~` (unary)
2. `<< >>`
3. `&`
4. `^`
5. `|`
6. `* / %`
7. `+ -`
8. `< > <= >=`
9. `== !=`
10. `&&`
11. `||`

## Predefined Symbols
| Symbol | Description |
|--------|-------------|
| `__VASM` | CPU feature bitfield |
| `REPTN` | Repeat iteration (-1 outside) |
| `NARG` | Macro argument count |
| `CARG` | Current macro argument index |
| `__SO` / `__RS` / `__FO` | Structure/register/frame offsets |

## Key Quirks
- Instructions auto-align to word boundary (disable: `-noialign`)
- CLR on 68000 does read-modify-write — disabled by default
- Single-pass: `if1` always true, `if2` always false
- Macro parameter substitution occurs even in comments
- Label must not start at column 1 if it's a mnemonic/directive
- Right-shift is signed unless `-unsshift`
- `hunkexe` can't resolve common symbols (use `hunk` + linker)
