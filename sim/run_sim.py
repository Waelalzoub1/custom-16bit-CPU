#!/usr/bin/env python3
"""Assemble every programs/*.asm, simulate CPU_export.v with Icarus Verilog,
and assert the final register/memory state against programs/expected.json."""
import json, os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
exp = json.load(open('programs/expected.json'))
subprocess.check_call(['iverilog', '-g2012', '-o', 'sim/cpu.vvp', 'sim/tb.v', 'CPU_export.v'])
fails = 0
for name, e in exp.items():
    subprocess.check_call([sys.executable, 'asm/asm.py', f'programs/{name}.asm', '-o', f'programs/{name}.hex'])
    words = open(f'programs/{name}.hex').read().split()[2:]          # drop "v2.0 raw"
    open(f'programs/{name}.mem', 'w').write('\n'.join(words) + '\n')  # $readmemh format
    out = subprocess.run(['vvp', 'sim/cpu.vvp', f'+prog=programs/{name}.mem', f'+cycles={e.get("cycles", 5000)}',
                          f'+mem_lo={e.get("mem_lo", 0)}', f'+mem_hi={e.get("mem_hi", 0)}'],
                         capture_output=True, text=True).stdout
    regs = {m.group(1): int(m.group(2)) for m in re.finditer(r'^R(\d+) (\d+)$', out, re.M)}
    mem = {m.group(1): int(m.group(2)) for m in re.finditer(r'^MEM (\d+) (\d+)$', out, re.M)}
    halted = re.search(r'^HALTED (\d)$', out, re.M).group(1) == '1'
    pc = re.search(r'^PC (\d+)$', out, re.M).group(1)
    cyc = re.search(r'^CYCLES (\d+)$', out, re.M).group(1)
    problems = []
    if e.get('halted') and not halted: problems.append(f'did not halt (PC={pc})')
    for r, v in e.get('regs', {}).items():
        if regs.get(r) != v: problems.append(f'R{r}={regs.get(r)} expected {v}')
    for a, v in e.get('mem', {}).items():
        if mem.get(a) != v: problems.append(f'MEM[{a}]={mem.get(a)} expected {v}')
    status = 'PASS' if not problems else 'FAIL'
    fails += bool(problems)
    print(f'{status}  {name:6s} words={len(words):3d} cycles={cyc} PC={pc} halted={halted}' + (('  ' + '; '.join(problems[:6])) if problems else ''))
print(f'{len(exp) - fails}/{len(exp)} programs pass')
sys.exit(1 if fails else 0)
