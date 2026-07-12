# Instruction Set Architecture — 16-bit RISC

A fixed-length, single-word RISC machine. **Every instruction is exactly 16 bits.**
16 general registers (`R0`–`R15`), each 16 bits. Load/store architecture: only
`LOAD`/`STORE` touch memory; everything else is register-to-register.

## Word layout

Every instruction is one 16-bit word, split into four 4-bit fields:

```
 bit  15 14 13 12 | 11 10 9 8 | 7 6 5 4 | 3 2 1 0
      [   OP    ] | [ field1] | [field2]| [field3]
```

The fields map **directly and uniformly** onto the register file we built:

| Field | Bits | Register-file port |
|-------|------|--------------------|
| `RD`  | 11:8 | write address (decoder `sel`) |
| `RA`  | 7:4  | read port A (`MUXA` select) |
| `RB`  | 3:0  | read port B (`MUXB` select) |

`RA` always drives read port A, `RB` always read port B, `RD` always the write
port — no matter the opcode. That uniformity is the whole point of RISC: the
decoder never has to hunt for where a register number lives.

## Formats

| Format | Layout | Meaning |
|--------|--------|---------|
| **R** (register) | `OP · RD · RA · RB` | ALU op on two registers → RD |
| **M** (memory)   | `OP · RD · RA · —` / `OP · — · RA · RB` | register-indirect load/store |
| **I** (immediate)| `OP · RD · imm8` | 8-bit constant into RD (imm = bits 7:0) |
| **J** (jump)     | `OP · — · RA · —` | target address comes from register RA |

## Opcode table

| OP  | Mnem | Fmt | Operation | Flags set |
|-----|------|-----|-----------|-----------|
|`0000`|`NOP` | — | (do nothing) | — |
|`0001`|`ADD` | R | `RD = RA + RB` | Z N C V |
|`0010`|`SUB` | R | `RD = RA - RB` | Z N C V |
|`0011`|`AND` | R | `RD = RA & RB` | Z N |
|`0100`|`OR`  | R | `RD = RA \| RB` | Z N |
|`0101`|`XOR` | R | `RD = RA ^ RB` | Z N |
|`0110`|`NOT` | R | `RD = ~RA` (RB unused) | Z N |
|`0111`|`LOAD`| M | `RD = MEM[RA]` (RB unused) | — |
|`1000`|`STORE`| M | `MEM[RA] = RB` (RD unused) | — |
|`1001`|`LUI` | I | `RD = (imm8 << 8) \| (RD & 0x00FF)` | — |
|`1010`|`LDI` | I | `RD = imm8` (zero-extended, high byte cleared) | — |
|`1011`|`JMP` | J | `PC = RA` | — |
|`1100`|`JEQ` | J | `if Z:        PC = RA` | — |
|`1101`|`JNE` | J | `if !Z:       PC = RA` | — |
|`1110`|`JGT` | J | `if (!Z & N==V): PC = RA` | — |
|`1111`|`HLT` | — | halt (freeze PC / stop clock) | — |

Flags are computed from the ALU's **adder path**, so they're only meaningful
**after `ADD`/`SUB`** (`Z` zero, `N` negative, `C` carry, `V` overflow). The logic
ops (`AND`/`OR`/`XOR`/`NOT`) do **not** set usable flags — so to test a value,
compare it with `SUB` first, *then* branch. A **flags register** (added at the
datapath level, not in the ALU) latches `Z N C V` so a later branch can read the
result of an earlier compare.

## Building constants (LDI + LUI)

An 8-bit immediate fits in one word; a full 16-bit constant takes two:

```
LDI R1, 0x34      ; R1 = 0x0034   (low byte, clears high)
LUI R1, 0x12      ; R1 = 0x1234   (sets high byte, keeps low)
```

Small constants (0–255) need only the single `LDI`. `LUI` is a read-modify-write
on `RD` (it preserves the low byte), so the datapath reads `RD` before writing.

## Pseudo-instructions (assembler shorthand, not real opcodes)

| You write | Assembler emits | Why it works |
|-----------|-----------------|--------------|
| `MOV RD, RA` | `OR RD, RA, RA` | `RA \| RA = RA` |
| `NOP` | `0x0000` | opcode 0 does nothing |

`MOV` isn't a hardware instruction — dropping it freed opcode `1001` for `LUI`,
at zero cost (a copy is a single-cycle `OR`).

## Addressing & control flow

- **Memory** is register-indirect: the address is *in a register*.
  `LOAD R3, R7` reads `MEM[R7]` into `R3`. `STORE R7, R3` writes `R3` to `MEM[R7]`.
- **Jumps/branches** are register-indirect too: the target is `reg[RA]`, a full
  16-bit address. Load the target into a register first (or keep a loop-top
  address parked in one). The condition is read from the flags; the register
  supplies where to go.

## Example programs

Add two numbers:
```
LDI R1, 10        ; R1 = 10
LDI R2, 20        ; R2 = 20
ADD R3, R1, R2    ; R3 = 30
HLT
```

Copy a register (MOV):
```
OR  R4, R1, R1    ; R4 = R1
```

Count-down loop (R1 from 5 to 0), using R7 as the loop-top address:
```
LDI R1, 5         ; counter = 5
LDI R0, 0         ; constant 0 for compares
LDI R7, <loop>    ; R7 = address of the SUB below
loop:
SUB R1, R1, R8    ; R1 -= 1   (R8 holds 1; sets flags)
JNE R7            ; if R1 != 0, jump back to loop
HLT
```
