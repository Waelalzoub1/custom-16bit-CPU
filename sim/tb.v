// Testbench for CPU_export.v: loads a program into the unified RAM, runs the
// CPU for +cycles clock cycles, then dumps the register file and a memory
// window so a script can assert on the final state.
//   sim/run_sim.py passes the instance names Digital generated as macros (RAM, RF, FLAGS, IR), e.g.
//   iverilog -g2012 -DRAM=DIG_RAMDualAccess_i15 -DRF=DIG_RegisterFile_i13 -DFLAGS=flags_i10 -DIR=Instruction_reader_i4 -o sim/cpu.vvp sim/tb.v CPU_export.v
//   vvp sim/cpu.vvp +prog=programs/fib.mem +cycles=2000 +mem_lo=256 +mem_hi=280
`timescale 1ns/1ps
module tb;
  reg clock = 0, R = 0;
  CPU_export dut(.R(R), .clock(clock));
  integer cycles, i, mem_lo, mem_hi, halt_seen, last_pc, same;
  reg [1023:0] prog;
  initial begin
    if (!$value$plusargs("prog=%s", prog)) begin $display("need +prog="); $finish; end
    if (!$value$plusargs("cycles=%d", cycles)) cycles = 5000;
    if (!$value$plusargs("mem_lo=%d", mem_lo)) mem_lo = 0;
    if (!$value$plusargs("mem_hi=%d", mem_hi)) mem_hi = 0;
    for (i = 0; i < 65536; i = i + 1) dut.`RAM.memory[i] = 16'h0000;
    for (i = 0; i < 16; i = i + 1) dut.`RF.memory[i] = 16'h0000;
    $readmemh(prog, dut.`RAM.memory);
    // Release reset in the middle of the low phase: the registers are NOR latches, and dropping R in the
    // same instant as a clock edge is a set/hold race that a zero-delay simulator turns into an endless oscillation.
    R = 1; #20 clock = 1; #20 clock = 0; #20 clock = 1; #20 clock = 0; #10 R = 0; #10;
    // HLT freezes the program counter and the instruction register (write-enable = NOT halt),
    // so the testbench stops once the PC has not moved for 8 cycles.
    halt_seen = 0; last_pc = -1; same = 0;
    for (i = 0; i < cycles && !halt_seen; i = i + 1) begin
      #20 clock = 1; #20 clock = 0;
      if (dut.`IR.PC_OUT === last_pc) same = same + 1; else same = 0;
      last_pc = dut.`IR.PC_OUT;
      if (same >= 8) halt_seen = 1;
      if ($test$plusargs("trace")) $display("cyc %0d PC=%0d OP=%h", i, dut.`IR.PC_OUT, dut.`IR.OP);
    end
    $display("PC %0d", dut.`IR.PC_OUT);
    $display("CYCLES %0d", i);
    $display("HALTED %0d", halt_seen);
    $display("FLAGS Z=%0d N=%0d C=%0d V=%0d", dut.`FLAGS.Zf, dut.`FLAGS.Nf, dut.`FLAGS.Cf, dut.`FLAGS.Vf);
    for (i = 0; i < 16; i = i + 1) $display("R%0d %0d", i, dut.`RF.memory[i]);
    for (i = mem_lo; i < mem_hi; i = i + 1) $display("MEM %0d %0d", i, dut.`RAM.memory[i]);
    $finish;
  end
endmodule
