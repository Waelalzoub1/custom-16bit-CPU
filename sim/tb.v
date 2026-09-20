// Testbench for CPU_export.v: loads a program into the unified RAM, runs the
// CPU for +cycles clock cycles, then dumps the register file and a memory
// window so a script can assert on the final state.
//   iverilog -g2012 -o sim/cpu.vvp sim/tb.v CPU_export.v
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
    for (i = 0; i < 65536; i = i + 1) dut.DIG_RAMDualAccess_i14.memory[i] = 16'h0000;
    for (i = 0; i < 16; i = i + 1) dut.DIG_RegisterFile_i12.memory[i] = 16'h0000;
    $readmemh(prog, dut.DIG_RAMDualAccess_i14.memory);
    R = 1; #20 clock = 1; #20 clock = 0; #20 clock = 1; #20 clock = 0; R = 0;
    // HLT does not stop the exported CPU (the control unit's halt bit is
    // unconnected and the PC register's WE is tied high), so the testbench
    // stops clocking when the instruction register holds an HLT opcode.
    halt_seen = 0;
    for (i = 0; i < cycles && !halt_seen; i = i + 1) begin
      #20 clock = 1; #20 clock = 0;
      if (dut.s4 == 4'hF) halt_seen = 1;
      if ($test$plusargs("trace")) $display("cyc %0d PC=%0d OP=%h RD=%h RA=%h RB=%h regA=%h regB=%h wb=%h we=%b jmp=%b", i, dut.Instruction_reader_i4.PC_OUT, dut.s4, dut.s7, dut.s5, dut.s6, dut.s1, dut.s19, dut.s31, dut.s10, dut.s2);
    end
    $display("PC %0d", dut.Instruction_reader_i4.PC_OUT);
    $display("CYCLES %0d", i);
    $display("HALTED %0d", halt_seen);
    $display("FLAGS Z=%0d N=%0d C=%0d V=%0d", dut.flags_i9.Zf, dut.flags_i9.Nf, dut.flags_i9.Cf, dut.flags_i9.Vf);
    for (i = 0; i < 16; i = i + 1) $display("R%0d %0d", i, dut.DIG_RegisterFile_i12.memory[i]);
    for (i = mem_lo; i < mem_hi; i = i + 1) $display("MEM %0d %0d", i, dut.DIG_RAMDualAccess_i14.memory[i]);
    $finish;
  end
endmodule
