#!/usr/bin/env python3
"""Run every program in Digital's own simulation engine (headless) on CPU.dig and
assert the same expected final state that sim/run_sim.py checks on the Verilog export.

    python3 sim/digital/run_digital.py [path/to/Digital.jar]
"""
import json, os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
JAR = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/.local/share/digital-app/Digital/Digital.jar')
subprocess.check_call(['javac', '-cp', JAR, '-d', 'sim/digital', 'sim/digital/DigSim.java'], stderr=subprocess.DEVNULL)
exp = json.load(open('programs/expected.json'))
fails = 0
for name, e in exp.items():
    subprocess.check_call([sys.executable, 'asm/asm.py', f'programs/{name}.asm', '-o', f'programs/{name}.hex'], stdout=subprocess.DEVNULL)
    out = subprocess.run(['java', '-cp', JAR + ':sim/digital', 'DigSim', 'CPU.dig', f'programs/{name}.hex',
                          str(e.get('cycles', 5000)), str(e.get('mem_lo', 0)), str(e.get('mem_hi', 0))],
                         capture_output=True, text=True).stdout
    regs = {m.group(1): int(m.group(2)) for m in re.finditer(r'^R(\d+) (\d+)$', out, re.M)}
    mem = {m.group(1): int(m.group(2)) for m in re.finditer(r'^MEM (\d+) (\d+)$', out, re.M)}
    halted = re.search(r'^HALTED (\d)$', out, re.M).group(1) == '1'
    cyc = re.search(r'^CYCLES (\d+)$', out, re.M).group(1)
    problems = []
    if e.get('halted') and not halted: problems.append('did not halt')
    problems += [f'R{r}={regs.get(r)} expected {v}' for r, v in e.get('regs', {}).items() if regs.get(r) != v]
    problems += [f'MEM[{a}]={mem.get(a)} expected {v}' for a, v in e.get('mem', {}).items() if mem.get(a) != v]
    fails += bool(problems)
    print(f'{"PASS" if not problems else "FAIL"}  {name:6s} cycles={cyc} halted={halted}' + ('  ' + '; '.join(problems[:5]) if problems else ''))
print(f'{len(exp) - fails}/{len(exp)} programs pass in Digital\'s engine')
sys.exit(1 if fails else 0)
