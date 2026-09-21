#!/usr/bin/env python3
"""Derive CPU_export.dig from CPU.dig and regenerate CPU_export.v.

CPU_export.dig is CPU.dig without the memory-mapped GraphicCard (which Digital
cannot export to Verilog): the GraphicCard, its address splitter, its write-enable
AND gate, its constant, and the wires that only serve them are removed. Nothing is
added or rewired. The Verilog is then produced headlessly with Digital's own
generator (sim/digital/DigExport.java).

    python3 tools/make_export.py [path/to/Digital.jar]
"""
import os, subprocess, sys
import xml.etree.ElementTree as ET

JAR = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/.local/share/digital-app/Digital/Digital.jar')
ELEMENTS = {('GraphicCard', 1280, 100), ('AND.dig', 1240, 0), ('Const', 1240, 160), ('Splitter', 1160, 200)}
WIRES = {((900, 280), (1360, 280)), ((940, 240), (1140, 240)), ((980, -20), (1160, -20)), ((1000, 0), (1240, 0)),
         ((1140, 200), (1140, 240)), ((1140, 200), (1160, 200)), ((1160, -20), (1160, 140)), ((1160, 140), (1280, 140)),
         ((1180, 100), (1180, 200)), ((1180, 100), (1280, 100)), ((1180, 240), (1200, 240)), ((1200, 40), (1200, 240)),
         ((1200, 40), (1240, 40)), ((1220, 80), (1220, 120)), ((1220, 80), (1300, 80)), ((1220, 120), (1280, 120)),
         ((1240, 160), (1240, 180)), ((1240, 160), (1280, 160)), ((1240, 180), (1280, 180)), ((1300, 20), (1300, 80)),
         ((1340, 140), (1360, 140)), ((1360, 140), (1360, 280))}

import re
text = open('CPU.dig', encoding='utf-8').read()
found_e, found_w = set(), set()

def drop_element(m):
    el = ET.fromstring(m.group(0))
    key = (el.find('elementName').text, int(el.find('pos').get('x')), int(el.find('pos').get('y')))
    if key in ELEMENTS:
        found_e.add(key); return ''
    return m.group(0)

def drop_wire(m):
    w = ET.fromstring(m.group(0))
    a = (int(w.find('p1').get('x')), int(w.find('p1').get('y'))); b = (int(w.find('p2').get('x')), int(w.find('p2').get('y')))
    key = (min(a, b), max(a, b))
    if key in WIRES:
        found_w.add(key); return ''
    return m.group(0)

# Remove whole blocks textually so the rest of the file keeps Digital's own formatting.
text = re.sub(r'[ \t]*<visualElement>.*?</visualElement>\n', drop_element, text, flags=re.S)
text = re.sub(r'[ \t]*<wire>.*?</wire>\n', drop_wire, text, flags=re.S)
missing = (ELEMENTS - found_e) | (WIRES - found_w)
if missing:
    sys.exit('CPU.dig layout changed around the GraphicCard; update tools/make_export.py. Not found: %s' % sorted(missing, key=str))
open('CPU_export.dig', 'w', encoding='utf-8').write(text)
print('wrote CPU_export.dig (removed %d elements, %d wires)' % (len(found_e), len(found_w)))
subprocess.check_call(['javac', '-cp', JAR, '-d', 'sim/digital', 'sim/digital/DigExport.java'], stderr=subprocess.DEVNULL)
subprocess.check_call(['java', '-cp', JAR + ':sim/digital', 'DigExport', 'CPU_export.dig', 'CPU_export.v'],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print('wrote CPU_export.v')
