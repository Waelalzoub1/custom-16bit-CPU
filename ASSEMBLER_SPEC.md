# Assembler Specification — 16-bit RISC CPU

A spec sheet for `asm` — an assembler that turns human-readable assembly into the
Digital `v2.0 raw` hex file that loads into this CPU's instruction memory.

This document is the **build blueprint**. It defines the input language, the
encoding rules, and the passes required. It does not implement anything.
See `ISA.md` for the hardware instruction set this targets.

---

## 1. Goal

```
   source.asm   ──►   [ assembler ]   ──►   program.hex   ──►  load into CPU.dig
 (human text)                              (v2.0 raw hex)
```

Input: a text file of assembly mnemonics + labels + comments.
Output: a `v2.0 raw` hex file — one 16-bit instruction word per line, hex, **no
`0x` prefix**, that Digital's LogisimReader loads into the program RAM.

---

## 2. Output format (hard requirement)

```
v2.0 raw
a103
a201
1312
f000
```

- First line is literally `v2.0 raw`.
- Each following line is exactly one instruction word, lowercase hex, 1–4 digits,
  **no `0x`, no `0b`, no commas**. (Zero-padding to 4 digits is optional but tidy.)
- One word per line, in address order (word 0 first).
- Blank trailing newline is fine.

---

## 3. Source language

### 3.1 Lexical rules
- **Case-insensitive** mnemonics and register names (`add` == `ADD`, `r1` == `R1`).
- **Comments:** `;` to end of line. Strip before parsing.
- **Whitespace:** spaces/tabs separate tokens; commas between operands are
  optional but recommended (`ADD R3, R1, R2`).
- **One instruction per line.** Blank lines allowed.
- **Registers:** `R0`–`R15` (decimal 0–15). Reject `R16`+.
- **Numbers:** accept `decimal` (`42`), `0x` hex (`0x2A`), `0b` binary (`0b101010`).
  Negative decimals allowed for immediates (two's-complement into the field width).

### 3.2 Labels
- A label is `name:` at the start of a line (optionally followed by an instruction).
  ```
  loop:  SUB R1, R1, R8
  ```
- Label names: `[A-Za-z_][A-Za-z0-9_]*`. Case-**sensitive** (labels are symbols).
- A label's **value is the word-address** of the next emitted instruction
  (see §6 for why this is computed *after* NOP insertion).
- Labels are used as immediates: `LDI R7, loop` loads that address into R7.
  (Because jumps are register-indirect, you always materialize a target address
  into a register, then `JMP`/`JEQ`/… that register.)

---

## 4. Instruction word (recap from ISA.md)

```
 bit 15..12 | 11..8 | 7..4 | 3..0
   [ OP ]   | [ RD ]| [ RA]| [ RB ]
```

`RD` = write reg, `RA` = read-port-A, `RB` = read-port-B. Encoding is uniform:
every mnemonic writes its 4-bit register numbers into these fixed fields.

---

## 5. Mnemonic → encoding table

`d,a,b` = 4-bit register numbers of RD/RA/RB. `imm8` = low 8 bits of the immediate.
`hi,lo` = high/low nibble of imm8 (so imm8 = (hi<<4)|lo).

| Syntax | OP | Fields emitted | Word = |
|--------|----|----|--------|
| `NOP`              | 0000 | —          | `0x0000` |
| `ADD  Rd, Ra, Rb`  | 0001 | d,a,b      | `1<<12 \| d<<8 \| a<<4 \| b` |
| `SUB  Rd, Ra, Rb`  | 0010 | d,a,b      | `2..` |
| `AND  Rd, Ra, Rb`  | 0011 | d,a,b      | `3..` |
| `OR   Rd, Ra, Rb`  | 0100 | d,a,b      | `4..` |
| `XOR  Rd, Ra, Rb`  | 0101 | d,a,b      | `5..` |
| `NOT  Rd, Ra`      | 0110 | d,a,0      | `6<<12 \| d<<8 \| a<<4` |
| `LOAD Rd, Ra`      | 0111 | d,a,0      | `7..`  (Rd = MEM[Ra]) |
| `STORE Ra, Rb`     | 1000 | 0,a,b      | `8<<12 \| a<<4 \| b`  (MEM[Ra] = Rb) |
| `LUI  Rd, imm8`    | 1001 | d,hi,lo    | `9<<12 \| d<<8 \| imm8` |
| `LDI  Rd, imm8`    | 1010 | d,hi,lo    | `a<<12 \| d<<8 \| imm8` |
| `JMP  Ra`          | 1011 | 0,a,0      | `b<<12 \| a<<4` |
| `JEQ  Ra`          | 1100 | 0,a,0      | `c..` |
| `JNE  Ra`          | 1101 | 0,a,0      | `d..` |
| `JGT  Ra`          | 1110 | 0,a,0      | `e..` |
| `HLT`              | 1111 | —          | `0xf000` |

**Notes**
- For `LDI`/`LUI` the immediate is split into the RA (high nibble) and RB (low
  nibble) fields: `imm8` occupies bits 7:0, i.e. `(hi<<4)|lo`. Just write imm8
  into the low byte of the word.
- Operand-count validation per mnemonic (e.g. `NOT` takes 2, `ADD` takes 3,
  `JMP` takes 1, `NOP`/`HLT` take 0). Reject wrong counts.

---

## 6. ⚠️ Branch delay slot — the assembler's key job

**This CPU is a 2-stage pipeline: the instruction immediately after any taken
branch ALWAYS executes before the jump lands (a 1-instruction delay slot, like
MIPS).** The assembler must handle this so the programmer never has to.

**Rule: after every `JMP`, `JEQ`, `JNE`, `JGT`, automatically insert one `NOP`**
(unless the programmer explicitly opted to fill the slot — see below).

Because inserting NOPs shifts every later address, this **must happen before
label addresses are assigned**. Ordering:

1. Parse each line → intermediate instruction objects.
2. Expand pseudo-instructions (§7).
3. **Insert a NOP after each branch instruction.**
4. Assign a word-address to each instruction (0,1,2,…) and record `label → address`.
5. Encode; substitute label references with their numeric addresses.

Optional refinement (v2): allow `.delayslot` / an explicit annotation so an
advanced user can place a useful instruction in the slot instead of a NOP. Ship
the always-NOP version first.

Also warn (or forbid) a `HLT` placed directly after a branch — it lands in the
delay slot and stops early (this is a real footgun; see project notes).

---

## 7. Pseudo-instructions

| You write | Expands to | Notes |
|-----------|-----------|-------|
| `MOV Rd, Ra` | `OR Rd, Ra, Ra` | register copy |
| `NOP`        | `0x0000`        | real opcode 0 |
| `LI Rd, imm16` | `LDI Rd, imm16&0xFF` then, if `imm16>0xFF`, `LUI Rd, imm16>>8` | load a full 16-bit constant/address |

`LI` is important: labels/addresses can exceed 255, and a bare `LDI` only loads a
byte. `LI Rd, label` should emit `LDI`+`LUI` when the address needs the high byte,
or just `LDI` when it fits in 8 bits. (Remember `LDI` clears the high byte first,
then `LUI` sets it — order matters: **LDI before LUI**.)

Note: `LI` may expand to 2 words → it also shifts addresses, so expand it in the
same pass as NOP insertion (step 2/3 above) before address assignment.

---

## 8. Two-pass algorithm (pseudocode)

```
PASS 1 — build the word list + symbol table
  words = []            # each entry: encoded value OR a fixup {op, fields, labelref}
  symbols = {}          # label -> address
  for each source line:
      strip comment; skip blanks
      if line starts with "name:":  pending_label = name; line = rest
      if line is empty after label: 
          # label with no instruction -> binds to next word
          remember pending_label for next emitted word
          continue
      inst = parse(mnemonic, operands)
      expanded = expand_pseudo(inst)          # MOV, LI -> 1..2 words
      for w in expanded:
          if pending_label: symbols[pending_label]=len(words); pending_label=None
          words.append(w)
          if w.mnemonic in {JMP,JEQ,JNE,JGT}:
              words.append(NOP)               # delay slot
  # after loop, any pending_label binds to len(words) (end address)

PASS 2 — resolve + encode
  for w in words:
      if w has a labelref:  w.imm = symbols[w.labelref]   # error if undefined
      emit encode(w)  as 4-hex-digit line

WRITE  "v2.0 raw\n" + lines
```

Validation to include: undefined label, duplicate label, register out of range,
immediate out of range (imm8 must fit signed/unsigned 8 bits; `LI` handles 16),
unknown mnemonic, wrong operand count.

---

## 9. Worked example

Source (`countdown.asm`):
```
      LI   R1, 3          ; counter
      LI   R8, 1          ; step
      LI   R7, loop       ; loop-top address into R7
loop: SUB  R1, R1, R8     ; R1 -= 1, sets flags
      JNE  R7             ; if R1 != 0 -> loop   (delay slot auto-NOP after)
      HLT
```

After pseudo-expansion + NOP insertion + addressing:
```
addr  word   asm
 0    a103   LDI R1,3        (LI R1,3 -> fits in a byte, one word)
 1    a801   LDI R8,1
 2    a7??   LDI R7,<loop>   (loop resolves to addr 3)
 3    2118   SUB R1,R1,R8    <- loop
 4    d070   JNE R7
 5    0000   NOP             <- auto-inserted delay slot
 6    f000   HLT
```
`loop` = 3, so word 2 = `a703`. Emit:
```
v2.0 raw
a103
a801
a703
2118
d070
0000
f000
```

---

## 10. Suggested implementation notes

- Language: anything (Python is the obvious first cut — a ~150-line script).
- CLI: `asm input.asm -o program.hex` (default output `program.hex`).
- Keep the mnemonic table (§5) as a data structure `{name: (opcode, arity, format)}`
  so encoding is table-driven, not a big switch.
- Emit 4-digit zero-padded lowercase hex for readability.
- Nice-to-haves (later): a `.org N` directive, `EQU`/constants, a listing output
  (addr + hex + source, like §9's table), and the optional explicit delay-slot fill.

---

## 11. Open decisions to make before coding

1. **Delay slot:** always-NOP (simple, recommended v1) vs. explicit fill. → start always-NOP.
2. **`LI` addressing:** does the assembler always emit LDI+LUI for labels, or only
   when the address > 255? → emit LDI-only when it fits, add LUI when needed.
3. **Number sign:** are immediates treated unsigned (0–255) or signed (−128..127)
   for `LDI`? → support both, mask into 8 bits.
4. **Multiple files / includes?** → out of scope for v1.
