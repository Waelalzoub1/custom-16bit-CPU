; Draw a diagonal on the 10x10 memory-mapped framebuffer.
; In CPU.dig the GraphicCard (VRAM) is written when address bit 15 is set and
; takes the low 8 bits as pixel index (y*10 + x), so pixel (i,i) is at
; 0x8000 + 11*i. CPU_export.v has no GraphicCard, so the words land in RAM at
; the same addresses and the test asserts on them.
      li   r1, 0x8000     ; VRAM base
      li   r2, 11         ; stride for (i,i)
      li   r3, 0xF800     ; pixel value (red in RGB565)
      li   r4, 10         ; count
      li   r5, 1
      li   r6, loop
loop: store r1, r3
      add  r1, r1, r2
      sub  r4, r4, r5
      jne  r6
      hlt
