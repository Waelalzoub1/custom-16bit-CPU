# custom-16bit-CPU

A 16-bit RISC CPU built from a single NAND gate, in the Digital logic simulator.

A complete **16-bit RISC CPU** built from scratch in **[Digital](https://github.com/hneemann/Digital)**, starting from a single `NAND` gate. Every circuit is composed from the smaller ones beneath it, so the collection reads bottom-up as *how a working computer is built from one logic gate* — NAND → gates → adders/ALU → registers/memory → control → CPU.

> The gate-level foundation that everything higher up the stack — an OS, a compiler, a neural net — ultimately runs on. Part of a broader "transistors → transformers" body of work.

## How to open / view these

The files are `.dig` circuits made with **[Digital](https://github.com/hneemann/Digital)**, a free, open-source logic designer and simulator (Java).

1. Download Digital from the [releases page](https://github.com/hneemann/Digital/releases) (cross-platform `.zip`, needs Java 8+).
2. Run it: `java -jar Digital.jar`
3. **File → Open** any `.dig` file in this repo.
4. Press the **▶ run** (simulate) button, then click input pins to toggle bits and watch the outputs update live.

Tip: open a higher-level circuit (e.g. `CPU.dig`) and double-click a sub-component to drill down into the smaller circuit it's built from. Keep every `.dig` file in the same folder so those references resolve.

## What's inside

### Basic gates
`NAND` is the root — everything else is built from it. `NAND_transistor` is the same gate built from CMOS transistors (proof-of-craft); `NAND` itself uses a fast behavioral version so the full CPU simulates quickly.
From NAND: `NOT` · `AND` · `OR` · `NOR` · `XOR`, plus 16-bit-wide versions `AND16` · `OR16` · `NOT16` · `XOR16`.

### Multiplexers & decoders
`2-to-1-MUX` · `4-to-1-MUX` · `8-to-1-MUX`, and 16-bit-wide `16bit2-to-1MUX` · `16bit-8-to-1-MUX` · `16bit-16-to-1-MUX`; `3-to-8-decoder` · `4-to-16-decoder`.

### Arithmetic
`halfAdder` → `Parallel adder` (4-bit carry-lookahead) → `Full-add-sub` (16-bit add/subtract, built from four `Parallel adder`s) → **`ALU`** (add/sub, AND, OR, XOR, NOT, with Z/N/C/V flags). `Incrementer` is used by the program counter.

### Memory & sequential logic
`D-latch` → `flip-flop` (master-slave) → `Register` (16-bit, clean clock with a hold-mux for write-enable) → `memory` (16×16 register file; `memory8` is the earlier 8-register version).

### CPU
- **`CPU.dig`** — the full 16-bit RISC CPU: von Neumann unified instruction+data memory, register file, ALU, control unit, flags, branch logic, and a memory-mapped graphics framebuffer.
- `control` — decodes the 4-bit opcode into control signals (PLA-style, built on `4-to-16-decoder`).
- `flags` — the Z/N/C/V flag register (latched on compares).
- `branch` — evaluates branch conditions (JMP / JEQ / JNE / JGT) against the flags.
- `immediate` — builds immediate and LUI constants from the instruction fields.
- `writeback` — selects the value written back to a register (ALU / memory / immediate / LUI).
- `Program Counter` · `Instruction reader` — fetch and instruction sequencing.
- `CPU_export` — a variant of `CPU.dig` prepared for Verilog export (`CPU_export.v`), used to push the design through synthesis (Yosys) and an ASIC flow (OpenLane / sky130).

### ISA & docs
`ISA.md` — the 16-opcode instruction set. `ASSEMBLER_SPEC.md` — assembly syntax for the CPU's assembler.

### Legacy / reference
`datamem` — a scrapped Harvard-style data-memory wrapper, replaced by the unified von Neumann RAM inside `CPU.dig`.

## Instruction set (summary)

Fixed 16-bit words: `OP[15:12] RD[11:8] RA[7:4] RB[3:0]`.
Opcodes: `NOP ADD SUB AND OR XOR NOT LOAD STORE LUI LDI JMP JEQ JNE JGT HLT`.
Memory addresses and jump targets are register-indirect. Full details in [`ISA.md`](ISA.md).

## Suggested reading order

`NAND` → `NOT` / `AND` / `OR` → `NOR` / `XOR` → `halfAdder` → `Parallel adder` → `Full-add-sub` → `ALU` → `D-latch` → `flip-flop` → `Register` → `memory` → `Program Counter` → `Instruction reader` → `control` / `flags` / `branch` / `immediate` / `writeback` → **`CPU`**.

---

<sub>Author: [Wael Alzoubi](https://github.com/Waelalzoub1) · part of a broader "transistors → transformers" body of work — see also [mini-os32](https://github.com/Waelalzoub1/mini-os32) and a [character-level transformer](https://github.com/Waelalzoub1/Transformer-character-level).</sub>
