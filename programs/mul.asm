; Multiply 123 x 45 by shift-and-add. The ISA has no shift, so "shift left"
; is x + x, and the multiplier bit test uses a mask that doubles each round.
; Result 5535 in R3 and at MEM[0x200].
      li   r0, 0          ; constant 0 (for compares)
      li   r1, 123        ; a (multiplicand, doubles each round)
      li   r2, 45         ; m (multiplier)
      li   r3, 0          ; result
      li   r4, 1          ; mask
      li   r5, 16         ; rounds
      li   r6, 1          ; constant 1
      li   r7, loop
      li   r8, skip
loop: and  r9, r2, r4     ; t = m & mask
      sub  r10, r9, r0    ; compare t with 0 (AND does not set usable flags)
      jeq  r8             ; bit clear -> skip
      add  r3, r3, r1     ; result += a
skip: add  r1, r1, r1     ; a <<= 1
      add  r4, r4, r4     ; mask <<= 1
      sub  r5, r5, r6     ; rounds--
      jne  r7
      li   r9, 0x200
      store r9, r3
      hlt
