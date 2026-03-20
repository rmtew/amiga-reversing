"""Generated runtime M68K compute knowledge artifact. Do not edit directly."""

from __future__ import annotations

from enum import StrEnum

from typing import TypeAlias

class ComputeOp(StrEnum):
    ADD = 'add'
    ADD_DECIMAL = 'add_decimal'
    ASSIGN = 'assign'
    BIT_CHANGE = 'bit_change'
    BIT_CLEAR = 'bit_clear'
    BIT_SET = 'bit_set'
    BIT_TEST = 'bit_test'
    BITWISE_AND = 'bitwise_and'
    BITWISE_COMPLEMENT = 'bitwise_complement'
    BITWISE_OR = 'bitwise_or'
    BITWISE_XOR = 'bitwise_xor'
    DIVIDE = 'divide'
    EXCHANGE = 'exchange'
    MULTIPLY = 'multiply'
    ROTATE = 'rotate'
    ROTATE_EXTEND = 'rotate_extend'
    SHIFT = 'shift'
    SIGN_EXTEND = 'sign_extend'
    SUBTRACT = 'subtract'
    SUBTRACT_DECIMAL = 'subtract_decimal'
    TEST = 'test'

class FormulaTerm(StrEnum):
    SOURCE = 'source'
    DESTINATION = 'destination'
    EXTEND = 'X'
    IMPLICIT = 'implicit'

class TruncationMode(StrEnum):
    TOWARD_ZERO = 'toward_zero'
class PrimaryDataSizeKind(StrEnum):
    MULTIPLY = 'multiply'
    DIVIDE = 'divide'
class OperationType(StrEnum):
    ADD = 'add'
    ADD_DECIMAL = 'add_decimal'
    ADDX = 'addx'
    AND = 'and'
    BIT_TEST = 'bit_test'
    BITFIELD = 'bitfield'
    BOUNDS_CHECK = 'bounds_check'
    CCR_OP = 'ccr_op'
    CLEAR = 'clear'
    COMPARE = 'compare'
    COMPARE_SWAP = 'compare_swap'
    DIVIDE = 'divide'
    MOVE = 'move'
    MULTIPLY = 'multiply'
    NEG = 'neg'
    NEGX = 'negx'
    NOT = 'not'
    OR = 'or'
    ROTATE = 'rotate'
    ROTATE_EXTEND = 'rotate_extend'
    SHIFT = 'shift'
    SIGN_EXTEND = 'sign_extend'
    SR_OP = 'sr_op'
    SUB = 'sub'
    SUB_DECIMAL = 'sub_decimal'
    SUBX = 'subx'
    SWAP = 'swap'
    TEST = 'test'
    XOR = 'xor'
class SpEffectAction(StrEnum):
    DECREMENT = 'decrement'
    INCREMENT = 'increment'
    ADJUST = 'adjust'
    SAVE_TO_REG = 'save_to_reg'
    LOAD_FROM_REG = 'load_from_reg'
ComputeFormula: TypeAlias = tuple[ComputeOp, tuple[FormulaTerm | int, ...], tuple[int, int] | None, tuple[int, int] | None, tuple[tuple[str, int], ...], TruncationMode | None]
PrimaryDataSize: TypeAlias = tuple[PrimaryDataSizeKind, int, int, int]
SpEffect: TypeAlias = tuple[SpEffectAction, int | None, str | None]

OPERATION_TYPES = {'ABCD': OperationType.ADD_DECIMAL,
 'ADD': OperationType.ADD,
 'ADDA': OperationType.ADD,
 'ADDI': OperationType.ADD,
 'ADDQ': OperationType.ADD,
 'ADDX': OperationType.ADDX,
 'AND': OperationType.AND,
 'ANDI': OperationType.AND,
 'ANDI to CCR': OperationType.CCR_OP,
 'ANDI to SR': OperationType.SR_OP,
 'ASL, ASR': OperationType.SHIFT,
 'BCHG': OperationType.BIT_TEST,
 'BCLR': OperationType.BIT_TEST,
 'BFCHG': OperationType.BITFIELD,
 'BFCLR': OperationType.BITFIELD,
 'BFEXTS': OperationType.BITFIELD,
 'BFEXTU': OperationType.BITFIELD,
 'BFFFO': OperationType.BITFIELD,
 'BFINS': OperationType.BITFIELD,
 'BFSET': OperationType.BITFIELD,
 'BFTST': OperationType.BITFIELD,
 'BKPT': None,
 'BRA': OperationType.ADD,
 'BSET': OperationType.BIT_TEST,
 'BSR': OperationType.SUB,
 'BTST': OperationType.BIT_TEST,
 'Bcc': None,
 'CALLM': None,
 'CAS CAS2': OperationType.COMPARE_SWAP,
 'CHK': OperationType.BOUNDS_CHECK,
 'CHK2': OperationType.BOUNDS_CHECK,
 'CINV': OperationType.SR_OP,
 'CLR': OperationType.CLEAR,
 'CMP': OperationType.COMPARE,
 'CMP2': OperationType.BOUNDS_CHECK,
 'CMPA': OperationType.COMPARE,
 'CMPI': OperationType.COMPARE,
 'CMPM': OperationType.COMPARE,
 'CPUSH': OperationType.SR_OP,
 'DBcc': None,
 'DIVS, DIVSL': OperationType.DIVIDE,
 'DIVU, DIVUL': OperationType.DIVIDE,
 'EOR': OperationType.XOR,
 'EORI': OperationType.XOR,
 'EORI to CCR': OperationType.CCR_OP,
 'EORI to SR': OperationType.SR_OP,
 'EXG': OperationType.SWAP,
 'EXT, EXTB': OperationType.SIGN_EXTEND,
 'FRESTORE': OperationType.SR_OP,
 'FSAVE': OperationType.SR_OP,
 'ILLEGAL': OperationType.SUB,
 'JMP': OperationType.MOVE,
 'JSR': OperationType.SUB,
 'LEA': OperationType.MOVE,
 'LINK': OperationType.SUB,
 'LSL, LSR': OperationType.SHIFT,
 'MOVE': OperationType.MOVE,
 'MOVE USP': OperationType.SR_OP,
 'MOVE from CCR': OperationType.CCR_OP,
 'MOVE from SR': OperationType.MOVE,
 'MOVE to CCR': OperationType.CCR_OP,
 'MOVE to SR': OperationType.SR_OP,
 'MOVE16': OperationType.MOVE,
 'MOVEA': OperationType.MOVE,
 'MOVEC': OperationType.SR_OP,
 'MOVEM': OperationType.MOVE,
 'MOVEP': OperationType.MOVE,
 'MOVEQ': OperationType.MOVE,
 'MOVES': OperationType.SR_OP,
 'MULS': OperationType.MULTIPLY,
 'MULU': OperationType.MULTIPLY,
 'NBCD': OperationType.NEGX,
 'NEG': OperationType.NEG,
 'NEGX': OperationType.NEGX,
 'NOP': None,
 'NOT': OperationType.NOT,
 'OR': OperationType.OR,
 'ORI': OperationType.OR,
 'ORI to CCR': OperationType.CCR_OP,
 'ORI to SR': OperationType.SR_OP,
 'PACK': OperationType.ADD,
 'PBcc': OperationType.SR_OP,
 'PDBcc': OperationType.SR_OP,
 'PEA': OperationType.SUB,
 'PFLUSH': OperationType.SR_OP,
 'PFLUSH PFLUSHA': OperationType.SR_OP,
 'PFLUSHR': OperationType.SR_OP,
 'PLOAD': OperationType.SR_OP,
 'PMOVE': OperationType.SR_OP,
 'PRESTORE': OperationType.SR_OP,
 'PSAVE': OperationType.SR_OP,
 'PScc': OperationType.SR_OP,
 'PTEST': OperationType.SR_OP,
 'PTRAPcc': OperationType.SR_OP,
 'PVALID': OperationType.MOVE,
 'RESET': OperationType.SR_OP,
 'ROL, ROR': OperationType.ROTATE,
 'ROXL, ROXR': OperationType.ROTATE_EXTEND,
 'RTD': OperationType.ADD,
 'RTE': OperationType.SR_OP,
 'RTM': None,
 'RTR': OperationType.CCR_OP,
 'RTS': OperationType.ADD,
 'SBCD': OperationType.SUB_DECIMAL,
 'STOP': OperationType.SR_OP,
 'SUB': OperationType.SUB,
 'SUBA': OperationType.SUB,
 'SUBI': OperationType.SUB,
 'SUBQ': OperationType.SUB,
 'SUBX': OperationType.SUBX,
 'SWAP': OperationType.SWAP,
 'Scc': None,
 'TAS': OperationType.TEST,
 'TRAP': OperationType.MOVE,
 'TRAPV': None,
 'TRAPcc': None,
 'TST': OperationType.TEST,
 'UNLK': OperationType.ADD,
 'UNPK': OperationType.ADD,
 'cpBcc': None,
 'cpDBcc': None,
 'cpGEN': None,
 'cpRESTORE': OperationType.SR_OP,
 'cpSAVE': OperationType.SR_OP,
 'cpScc': None,
 'cpTRAPcc': None}
COMPUTE_FORMULAS = {'ABCD': (ComputeOp.ADD_DECIMAL, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION, FormulaTerm.EXTEND), None, None, (), None),
 'ADD': (ComputeOp.ADD, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'ADDA': (ComputeOp.ADD, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'ADDI': (ComputeOp.ADD, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'ADDQ': (ComputeOp.ADD, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'ADDX': (ComputeOp.ADD, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION, FormulaTerm.EXTEND), None, None, (), None),
 'AND': (ComputeOp.BITWISE_AND, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'ANDI': (ComputeOp.BITWISE_AND, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'ASL, ASR': (ComputeOp.SHIFT, (), None, None, (), None),
 'BCHG': (ComputeOp.BIT_CHANGE, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'BCLR': (ComputeOp.BIT_CLEAR, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'BRA': (ComputeOp.ADD, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'BSET': (ComputeOp.BIT_SET, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'BTST': (ComputeOp.BIT_TEST, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'CLR': (ComputeOp.ASSIGN, (FormulaTerm.IMPLICIT,), None, None, (), None),
 'CMP': (ComputeOp.SUBTRACT, (FormulaTerm.DESTINATION, FormulaTerm.SOURCE), None, None, (), None),
 'CMPA': (ComputeOp.SUBTRACT, (FormulaTerm.DESTINATION, FormulaTerm.SOURCE), None, None, (), None),
 'CMPI': (ComputeOp.SUBTRACT, (FormulaTerm.DESTINATION, FormulaTerm.SOURCE), None, None, (), None),
 'CMPM': (ComputeOp.SUBTRACT, (FormulaTerm.DESTINATION, FormulaTerm.SOURCE), None, None, (), None),
 'DIVS, DIVSL': (ComputeOp.DIVIDE, (FormulaTerm.DESTINATION, FormulaTerm.SOURCE), None, None, (), TruncationMode.TOWARD_ZERO),
 'DIVU, DIVUL': (ComputeOp.DIVIDE, (FormulaTerm.DESTINATION, FormulaTerm.SOURCE), None, None, (), TruncationMode.TOWARD_ZERO),
 'EOR': (ComputeOp.BITWISE_XOR, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'EORI': (ComputeOp.BITWISE_XOR, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'EXT, EXTB': (ComputeOp.SIGN_EXTEND, (FormulaTerm.DESTINATION,), None, None, (('w', 8), ('l', 16), ('extb_l', 8)), None),
 'JMP': (ComputeOp.ASSIGN, (FormulaTerm.SOURCE,), None, None, (), None),
 'LEA': (ComputeOp.ASSIGN, (FormulaTerm.SOURCE,), None, None, (), None),
 'LSL, LSR': (ComputeOp.SHIFT, (), None, None, (), None),
 'MOVE': (ComputeOp.ASSIGN, (FormulaTerm.SOURCE,), None, None, (), None),
 'MOVE from SR': (ComputeOp.ASSIGN, (FormulaTerm.SOURCE,), None, None, (), None),
 'MOVE16': (ComputeOp.ASSIGN, (FormulaTerm.SOURCE,), None, None, (), None),
 'MOVEA': (ComputeOp.ASSIGN, (FormulaTerm.SOURCE,), None, None, (), None),
 'MOVEM': (ComputeOp.ASSIGN, (FormulaTerm.SOURCE,), None, None, (), None),
 'MOVEP': (ComputeOp.ASSIGN, (FormulaTerm.SOURCE,), None, None, (), None),
 'MOVEQ': (ComputeOp.ASSIGN, (FormulaTerm.SOURCE,), None, None, (), None),
 'MULS': (ComputeOp.MULTIPLY, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'MULU': (ComputeOp.MULTIPLY, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'NBCD': (ComputeOp.SUBTRACT_DECIMAL, (FormulaTerm.IMPLICIT, FormulaTerm.DESTINATION, FormulaTerm.EXTEND), None, None, (), None),
 'NEG': (ComputeOp.SUBTRACT, (FormulaTerm.IMPLICIT, FormulaTerm.DESTINATION), None, None, (), None),
 'NEGX': (ComputeOp.SUBTRACT, (FormulaTerm.IMPLICIT, FormulaTerm.DESTINATION, FormulaTerm.EXTEND), None, None, (), None),
 'NOT': (ComputeOp.BITWISE_COMPLEMENT, (FormulaTerm.DESTINATION,), None, None, (), None),
 'OR': (ComputeOp.BITWISE_OR, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'ORI': (ComputeOp.BITWISE_OR, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'PACK': (ComputeOp.ADD, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None),
 'PEA': (ComputeOp.SUBTRACT, (FormulaTerm.DESTINATION, FormulaTerm.SOURCE), None, None, (), None),
 'PVALID': (ComputeOp.ASSIGN, (FormulaTerm.SOURCE,), None, None, (), None),
 'ROL, ROR': (ComputeOp.ROTATE, (), None, None, (), None),
 'ROXL, ROXR': (ComputeOp.ROTATE_EXTEND, (), None, None, (), None),
 'SBCD': (ComputeOp.SUBTRACT_DECIMAL, (FormulaTerm.DESTINATION, FormulaTerm.SOURCE, FormulaTerm.EXTEND), None, None, (), None),
 'SUB': (ComputeOp.SUBTRACT, (FormulaTerm.DESTINATION, FormulaTerm.SOURCE), None, None, (), None),
 'SUBA': (ComputeOp.SUBTRACT, (FormulaTerm.DESTINATION, FormulaTerm.SOURCE), None, None, (), None),
 'SUBI': (ComputeOp.SUBTRACT, (FormulaTerm.DESTINATION, FormulaTerm.SOURCE), None, None, (), None),
 'SUBQ': (ComputeOp.SUBTRACT, (FormulaTerm.DESTINATION, FormulaTerm.SOURCE), None, None, (), None),
 'SUBX': (ComputeOp.SUBTRACT, (FormulaTerm.DESTINATION, FormulaTerm.SOURCE, FormulaTerm.EXTEND), None, None, (), None),
 'SWAP': (ComputeOp.EXCHANGE, (), (31, 16), (15, 0), (), None),
 'TAS': (ComputeOp.TEST, (FormulaTerm.DESTINATION,), None, None, (), None),
 'TRAP': (ComputeOp.ASSIGN, (FormulaTerm.SOURCE,), None, None, (), None),
 'TST': (ComputeOp.TEST, (FormulaTerm.DESTINATION,), None, None, (), None),
 'UNPK': (ComputeOp.ADD, (FormulaTerm.SOURCE, FormulaTerm.DESTINATION), None, None, (), None)}
IMPLICIT_OPERANDS = {'CLR': 0, 'NBCD': 0, 'NEG': 0, 'NEGX': 0}
SP_EFFECTS = {'BSR': ((SpEffectAction.DECREMENT, 4, None),),
 'ILLEGAL': ((SpEffectAction.DECREMENT, 2, None),),
 'JSR': ((SpEffectAction.DECREMENT, 4, None),),
 'LINK': ((SpEffectAction.DECREMENT, 4, None), (SpEffectAction.SAVE_TO_REG, None, 'An'), (SpEffectAction.ADJUST, None, 'd'),),
 'PEA': ((SpEffectAction.DECREMENT, 4, None),),
 'RTD': ((SpEffectAction.INCREMENT, 4, None), (SpEffectAction.ADJUST, None, 'd'),),
 'RTR': ((SpEffectAction.INCREMENT, 2, None), (SpEffectAction.INCREMENT, 4, None),),
 'RTS': ((SpEffectAction.INCREMENT, 4, None),),
 'UNLK': ((SpEffectAction.LOAD_FROM_REG, None, 'An'), (SpEffectAction.INCREMENT, 4, None),)}
PRIMARY_DATA_SIZES = {'DIVS, DIVSL': (PrimaryDataSizeKind.DIVIDE, 16, 32, 16),
 'DIVU, DIVUL': (PrimaryDataSizeKind.DIVIDE, 16, 32, 16),
 'MULS': (PrimaryDataSizeKind.MULTIPLY, 16, 16, 32),
 'MULU': (PrimaryDataSizeKind.MULTIPLY, 16, 16, 32)}
