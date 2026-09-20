; Bubble sort 8 words in place at MEM[0x300..0x307].
; Input 9,3,7,1,8,2,6,4 is written by the program itself (no .data directive).
      li   r15, 1         ; constant 1
      li   r1, 0x300      ; base
      mov  r2, r1
      li   r3, 9
      store r2, r3
      add  r2, r2, r15
      li   r3, 3
      store r2, r3
      add  r2, r2, r15
      li   r3, 7
      store r2, r3
      add  r2, r2, r15
      li   r3, 1
      store r2, r3
      add  r2, r2, r15
      li   r3, 8
      store r2, r3
      add  r2, r2, r15
      li   r3, 2
      store r2, r3
      add  r2, r2, r15
      li   r3, 6
      store r2, r3
      add  r2, r2, r15
      li   r3, 4
      store r2, r3
      li   r14, 7         ; pass = n-1
      li   r10, outer
      li   r11, inner
      li   r12, noswap
outer: mov  r2, r1        ; p = base
      mov  r3, r14        ; j = pass
inner: load r4, r2        ; x = MEM[p]
      add  r5, r2, r15    ; q = p + 1
      load r6, r5         ; y = MEM[q]
      sub  r7, r6, r4     ; y - x
      jgt  r12            ; y > x -> already ordered
      store r2, r6        ; swap
      store r5, r4
noswap: mov r2, r5        ; p++
      sub  r3, r3, r15    ; j--
      jne  r11
      sub  r14, r14, r15  ; pass--
      jne  r10
      hlt
