; Fibonacci: store F(0)..F(23) at MEM[0x100..0x117]; ends with R1 = F(24) = 46368
      li   r1, 0          ; a = F(0)
      li   r2, 1          ; b = F(1)
      li   r3, 0x100      ; ptr
      li   r4, 24         ; count
      li   r5, 1          ; constant 1
      li   r6, loop
loop: store r3, r1        ; MEM[ptr] = a
      add  r7, r1, r2     ; t = a + b
      mov  r1, r2         ; a = b
      mov  r2, r7         ; b = t
      add  r3, r3, r5     ; ptr++
      sub  r4, r4, r5     ; count-- (sets Z)
      jne  r6             ; loop while count != 0
      hlt
