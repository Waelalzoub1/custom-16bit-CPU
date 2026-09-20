#!/usr/bin/env python3
"""Walk the .dig hierarchy from CPU.dig and count leaf primitives (NAND gates
and Digital built-ins) per sub-circuit. Run from the repository root."""
import collections, xml.etree.ElementTree as ET
memo = {}
def elems(fn): return [e.find('elementName').text for e in ET.parse(fn).getroot().iter('visualElement')]
def leaves(fn):
    if fn in memo: return memo[fn]
    c = collections.Counter()
    for e in elems(fn):
        if e.endswith('.dig'): c.update(leaves(e))
        else: c[e] += 1
    memo[fn] = c; return c
WIRING = {'In', 'Out', 'Splitter', 'Const', 'Ground', 'VDD', 'Clock', 'Text', 'Tunnel', 'Probe'}
for sub in ['ALU.dig', 'Full-add-sub.dig', 'Register.dig', 'memory.dig', 'Instruction reader.dig', 'control.dig',
            'branch.dig', 'writeback.dig', 'immediate.dig', 'flags.dig', 'CPU.dig']:
    c = leaves(sub)
    builtins = {k: v for k, v in c.items() if k not in WIRING and k != 'NAnd'}
    print(f'{sub:24s} NAND={c["NAnd"]:6d}  built-ins={builtins}')
n = leaves('CPU.dig')['NAnd']
print(f'\nCPU.dig: {n} NAND gates = {n*4} transistors at 4 per NAND (NAND_transistor.dig)')
