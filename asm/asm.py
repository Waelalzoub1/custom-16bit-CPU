#!/usr/bin/env python3
"""Two-pass assembler for the 16-bit RISC CPU, following ASSEMBLER_SPEC.md.

    asm.py input.asm [-o program.hex] [--listing]

Output is Digital's "v2.0 raw" format: one 16-bit word per line as 4 lowercase
hex digits. A NOP is inserted after every branch (JMP/JEQ/JNE/JGT) because the
CPU executes the instruction after a taken branch (1-slot branch delay).
"""
import argparse, re, sys

# mnemonic -> (opcode, operand kinds)
#   'd' = RD register, 'a' = RA register, 'b' = RB register, 'i' = imm8 (or label)
TABLE = {
    'NOP':   (0x0, ''),
    'ADD':   (0x1, 'dab'),
    'SUB':   (0x2, 'dab'),
    'AND':   (0x3, 'dab'),
    'OR':    (0x4, 'dab'),
    'XOR':   (0x5, 'dab'),
    'NOT':   (0x6, 'da'),
    'LOAD':  (0x7, 'da'),
    'STORE': (0x8, 'ab'),
    'LUI':   (0x9, 'di'),
    'LDI':   (0xA, 'di'),
    'JMP':   (0xB, 'a'),
    'JEQ':   (0xC, 'a'),
    'JNE':   (0xD, 'a'),
    'JGT':   (0xE, 'a'),
    'HLT':   (0xF, ''),
}
BRANCHES = {'JMP', 'JEQ', 'JNE', 'JGT'}
LABEL_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

class AsmError(Exception):
    pass

class Word:
    """One emitted instruction word, possibly with an unresolved label."""
    def __init__(self, mnem, d=0, a=0, b=0, imm=None, label=None, lui=False, line=0, src=''):
        self.mnem, self.d, self.a, self.b, self.imm, self.label, self.lui, self.line, self.src = \
            mnem, d, a, b, imm, label, lui, line, src

def parse_reg(tok, line):
    m = re.fullmatch(r'[Rr](\d+)', tok)
    if not m: raise AsmError(f'line {line}: expected register, got {tok!r}')
    n = int(m.group(1))
    if n > 15: raise AsmError(f'line {line}: register R{n} out of range (R0-R15)')
    return n

def parse_num(tok, line):
    t = tok.lower(); neg = t.startswith('-'); t = t.lstrip('-')
    try:
        if t.startswith('0x'): v = int(t, 16)
        elif t.startswith('0b'): v = int(t, 2)
        elif t.isdigit(): v = int(t, 10)
        else: return None
    except ValueError:
        return None
    return -v if neg else v

def fit(v, bits, line, what):
    lo, hi = -(1 << (bits - 1)), (1 << bits) - 1
    if not lo <= v <= hi: raise AsmError(f'line {line}: {what} {v} does not fit in {bits} bits')
    return v & ((1 << bits) - 1)

def parse_line(raw, lineno, words, symbols, pending):
    text = raw.split(';', 1)[0].strip()
    if not text: return
    if ':' in text:
        label, _, text = text.partition(':')
        label = label.strip()
        if not LABEL_RE.match(label): raise AsmError(f'line {lineno}: bad label {label!r}')
        if label in symbols or label in pending: raise AsmError(f'line {lineno}: duplicate label {label!r}')
        pending.append(label)
        text = text.strip()
        if not text: return
    toks = [t for t in re.split(r'[,\s]+', text) if t]
    mnem, ops = toks[0].upper(), toks[1:]
    emitted = []
    if mnem == 'MOV':
        if len(ops) != 2: raise AsmError(f'line {lineno}: MOV takes 2 operands')
        d, a = parse_reg(ops[0], lineno), parse_reg(ops[1], lineno)
        emitted.append(Word('OR', d=d, a=a, b=a, line=lineno, src=text))
    elif mnem == 'LI':
        if len(ops) != 2: raise AsmError(f'line {lineno}: LI takes 2 operands')
        d = parse_reg(ops[0], lineno)
        v = parse_num(ops[1], lineno)
        if v is None:
            if not LABEL_RE.match(ops[1]): raise AsmError(f'line {lineno}: bad immediate {ops[1]!r}')
            # label: size unknown until pass 2 -> always emit LDI+LUI so addresses stay fixed
            emitted.append(Word('LDI', d=d, label=ops[1], line=lineno, src=text))
            emitted.append(Word('LUI', d=d, label=ops[1], lui=True, line=lineno, src=text))
        else:
            v = fit(v, 16, lineno, 'immediate')
            emitted.append(Word('LDI', d=d, imm=v & 0xFF, line=lineno, src=text))
            if v > 0xFF: emitted.append(Word('LUI', d=d, imm=v >> 8, line=lineno, src=text))
    elif mnem in TABLE:
        op, kinds = TABLE[mnem]
        if len(ops) != len(kinds): raise AsmError(f'line {lineno}: {mnem} takes {len(kinds)} operand(s), got {len(ops)}')
        w = Word(mnem, line=lineno, src=text)
        for kind, tok in zip(kinds, ops):
            if kind == 'd': w.d = parse_reg(tok, lineno)
            elif kind == 'a': w.a = parse_reg(tok, lineno)
            elif kind == 'b': w.b = parse_reg(tok, lineno)
            else:
                v = parse_num(tok, lineno)
                if v is None:
                    if not LABEL_RE.match(tok): raise AsmError(f'line {lineno}: bad immediate {tok!r}')
                    w.label = tok
                else:
                    w.imm = fit(v, 8, lineno, 'immediate')
        emitted.append(w)
    else:
        raise AsmError(f'line {lineno}: unknown mnemonic {mnem!r}')
    for w in emitted:
        if pending:
            for l in pending: symbols[l] = len(words)
            pending.clear()
        words.append(w)
        if w.mnem in BRANCHES:
            words.append(Word('NOP', line=lineno, src='(delay slot)'))
    if mnem == 'HLT' and len(words) >= 3 and words[-2].mnem in BRANCHES:
        pass  # HLT after a branch is fine here: the auto-NOP sits between them

def encode(w, symbols):
    op = TABLE[w.mnem][0]
    imm = w.imm
    if w.label is not None:
        if w.label not in symbols: raise AsmError(f'line {w.line}: undefined label {w.label!r}')
        addr = symbols[w.label]
        imm = (addr >> 8) & 0xFF if w.lui else addr & 0xFF
        if w.mnem in ('LDI', 'LUI') and not w.lui and addr > 0xFF and w.src.upper().startswith('LDI'):
            raise AsmError(f'line {w.line}: label {w.label!r} = {addr} does not fit in LDI imm8; use LI')
    if imm is not None:
        return (op << 12) | (w.d << 8) | (imm & 0xFF)
    return (op << 12) | (w.d << 8) | (w.a << 4) | w.b

def assemble(source):
    words, symbols, pending = [], {}, []
    for n, raw in enumerate(source.splitlines(), 1):
        parse_line(raw, n, words, symbols, pending)
    for l in pending: symbols[l] = len(words)
    if len(words) > 65536: raise AsmError('program exceeds 65536 words')
    return [encode(w, symbols) for w in words], words, symbols

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input'); ap.add_argument('-o', '--output', default='program.hex')
    ap.add_argument('--listing', action='store_true')
    a = ap.parse_args()
    try:
        codes, words, symbols = assemble(open(a.input).read())
    except AsmError as e:
        sys.exit(f'{a.input}: {e}')
    with open(a.output, 'w') as f:
        f.write('v2.0 raw\n' + ''.join(f'{c:04x}\n' for c in codes))
    if a.listing:
        for addr, (c, w) in enumerate(zip(codes, words)):
            print(f'{addr:4d}  {c:04x}  {w.src}')
        for k, v in symbols.items(): print(f'{k} = {v}')

if __name__ == '__main__':
    main()
