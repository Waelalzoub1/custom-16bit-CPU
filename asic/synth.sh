#!/usr/bin/env bash
# Generic-gate synthesis of the faithful Digital export with Yosys.
# The export has no outputs (the CPU only drives its internal RAM), so a
# wrapper exposing six datapath buses is generated first; otherwise Yosys
# removes the whole design as dead logic. Memories are kept as $mem cells so
# the count reflects the CPU logic, not 64K words of RAM turned into flops.
set -e
cd "$(dirname "$0")/.."
python3 - <<'PY'
s=open('CPU_export.v').read()
s=s.replace("module CPU_export (\n  input R,\n  input clock\n);","module CPU_export (\n  input R,\n  input clock,\n  output [15:0] o_regA, output [15:0] o_regB, output [15:0] o_wb, output [15:0] o_instr, output [15:0] o_memrd, output [15:0] o_pc\n);")
i=s.rindex("endmodule")
open('asic/CPU_export_obs.v','w').write(s[:i]+"  assign o_regA = s1; assign o_regB = s19; assign o_wb = s31; assign o_instr = s3; assign o_memrd = s30; assign o_pc = s8;\n"+s[i:])
PY
yosys -q -l asic/yosys_generic_stats.log -p "read_verilog asic/CPU_export_obs.v; hierarchy -check -top CPU_export; proc; flatten; opt; memory -nomap; opt -full; techmap; opt -full; abc -g AND,NAND,OR,NOR,XOR,XNOR,ANDNOT,ORNOT,MUX; opt_clean -purge; stat" >/dev/null
sed -n "$(grep -n 'Printing statistics' asic/yosys_generic_stats.log | tail -1 | cut -d: -f1),\$p" asic/yosys_generic_stats.log
