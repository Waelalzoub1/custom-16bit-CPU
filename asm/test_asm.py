#!/usr/bin/env python3
"""Unit tests for asm.py: run with `python3 asm/test_asm.py`."""
import sys, os, unittest
sys.path.insert(0, os.path.dirname(__file__))
from asm import assemble, AsmError

def hexes(src):
    return [f'{c:04x}' for c in assemble(src)[0]]

class TestEncoding(unittest.TestCase):
    def test_spec_worked_example(self):
        src = """
      LI   R1, 3          ; counter
      LI   R8, 1          ; step
      LI   R7, loop       ; loop-top address into R7
loop: SUB  R1, R1, R8     ; R1 -= 1, sets flags
      JNE  R7             ; if R1 != 0 -> loop
      HLT
"""
        # LI with a label always emits LDI+LUI (2 words) so loop = 4, not 3 as in the spec's
        # single-word example; both encodings are legal per spec section 7.
        self.assertEqual(hexes(src), ['a103', 'a801', 'a704', '9700', '2118', 'd070', '0000', 'f000'])

    def test_r_type(self):
        self.assertEqual(hexes('ADD R3, R1, R2'), ['1312'])
        self.assertEqual(hexes('sub r15, r14, r13'), ['2fed'])
        self.assertEqual(hexes('AND R1 R2 R3\nOR R1 R2 R3\nXOR R1 R2 R3'), ['3123', '4123', '5123'])
        self.assertEqual(hexes('NOT R4, R5'), ['6450'])

    def test_memory(self):
        self.assertEqual(hexes('LOAD R3, R7'), ['7370'])
        self.assertEqual(hexes('STORE R7, R3'), ['8073'])

    def test_immediates(self):
        self.assertEqual(hexes('LDI R1, 0x34\nLUI R1, 0x12'), ['a134', '9112'])
        self.assertEqual(hexes('LDI R2, 0b1010'), ['a20a'])
        self.assertEqual(hexes('LDI R2, -1'), ['a2ff'])
        self.assertEqual(hexes('LI R5, 0x1234'), ['a534', '9512'])
        self.assertEqual(hexes('LI R5, 200'), ['a5c8'])

    def test_branch_delay_slot(self):
        self.assertEqual(hexes('JMP R1\nHLT'), ['b010', '0000', 'f000'])
        self.assertEqual(hexes('JEQ R2\nJNE R3\nJGT R4'), ['c020', '0000', 'd030', '0000', 'e040', '0000'])

    def test_labels_account_for_inserted_nops(self):
        src = 'JMP R1\ntarget: HLT\n'
        codes, words, symbols = assemble(src)
        self.assertEqual(symbols['target'], 2)

    def test_pseudo_mov_and_nop_hlt(self):
        self.assertEqual(hexes('MOV R4, R1'), ['4411'])
        self.assertEqual(hexes('NOP\nHLT'), ['0000', 'f000'])

    def test_label_at_end_and_case(self):
        codes, words, symbols = assemble('nop\nEnd:\n')
        self.assertEqual(symbols['End'], 1)

    def test_errors(self):
        for bad in ['ADD R1, R2', 'FOO R1', 'LDI R1, 300', 'ADD R16, R1, R2', 'JMP nowhere_label_used_as_reg',
                    'LDI R1, missing', 'x: NOP\nx: NOP', 'LDI R1, 0x1FF']:
            with self.assertRaises(AsmError, msg=bad):
                assemble(bad)

if __name__ == '__main__':
    unittest.main(verbosity=1)
