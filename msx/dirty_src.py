DMAP=0x8300; ROWF=DMAP+448
SRC2 = f"""
; ---------- B15Fh: marcar celdas que toca cada pieza ----------
MARK:
  ld a,(ACTIVE)
  or a
  jp z,mk_end
  ld a,(OWNER)
  inc a
  jp nz,mk_do
  ld a,(LASTIDX)
  cp 3Eh
  jr c,mk_do
  cp 48h
  jr nc,mk_do
  ld hl,HSIG0
  ld a,(0D099h)
  cp 64
  jr c,mk_h
  ld hl,HSIG1
mk_h:
  ld a,(LASTIDX)
  ld b,a
  ld a,(0D098h)
  ld c,a
  ld a,(0D099h)
  ld d,a
  push hl
  ld a,(hl)
  cp b
  jr nz,mk_new
  inc hl
  ld a,(hl)
  cp c
  jr nz,mk_new
  inc hl
  ld a,(hl)
  cp d
  jr nz,mk_new
  pop hl
  jr mk_end
mk_new:
  pop hl
  ld (hl),b
  inc hl
  ld (hl),c
  inc hl
  ld (hl),d
mk_do:
  ld a,(0B1DFh)
  or a
  jp z,mk_end
  ld b,a
  ld a,(0B1E1h)
  or a
  jp z,mk_end
  ld c,a
  ld a,(0B1DEh)
  ld e,a
  add a,b
  dec a
  rrca
  rrca
  rrca
  and 1Fh
  ld d,a
  ld a,e
  rrca
  rrca
  rrca
  and 1Fh
  ld e,a
  ld a,d
  sub e
  inc a
  ld b,a
  ld hl,{ROWF}
  ld d,0
  add hl,de
  push hl
  ld l,e
  ld h,0
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  ld a,(0B1E0h)
  ld e,a
  add hl,de
  ld de,{DMAP}
  add hl,de
  pop de
mk_row:
  ld a,(de)
  or 1
  ld (de),a
  inc de
  push bc
  push hl
  ld b,c
mk_col:
  set 0,(hl)
  inc hl
  djnz mk_col
  pop hl
  ld bc,32
  add hl,bc
  pop bc
  djnz mk_row
mk_end:
  ld a,(0B1DFh)
  ret

; ---------- A521h: animacion del publico (escribe directo en el buffer) ----------
CROWD:
  push hl
  ld a,(ACTIVE)
  or a
  jr z,cr_end
  ld a,l
  and 1Fh
  ld e,a
  ld d,0
  ld hl,{DMAP + 32}
  add hl,de
  ld a,1
  ld ({ROWF + 1}),a
  ld ({ROWF + 2}),a
  ld ({ROWF + 3}),a
  ld ({ROWF + 4}),a
  ld c,4
cr_r:
  push hl
  ld b,11
cr_c:
  set 0,(hl)
  inc hl
  djnz cr_c
  pop hl
  ld de,32
  add hl,de
  dec c
  jr nz,cr_r
cr_end:
  pop hl
  ld de,0C298h
  ret

"""
SRC3 = f"""
; ---------- 8554h: inicio de fotograma del bucle principal ----------
MCOPY:
  ld a,(SYNC)
  or a
  jr nz,mc_sel
  call 0B1F2h
  ld hl,{DMAP}
  ld de,{DMAP + 1}
  ld bc,{448 + 14 - 1}
  ld (hl),0
  ldir
  ld a,1
  ld (FULLUP),a
  ret
mc_sel:
  call SPRINIT
  ld a,(ROLL)
  ld e,a
  ld d,0
  ld hl,{ROWF}
  add hl,de
  set 0,(hl)
  ld l,e
  ld h,d
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  ld de,{DMAP}
  add hl,de
  ld b,32
mc_rl:
  set 0,(hl)
  inc hl
  djnz mc_rl
  ld hl,{DMAP}
  ld de,{ROWF}
  ld c,0
mc_row:
  ld a,(de)
  or a
  jr nz,mc_scan
  ld a,l
  add a,32
  ld l,a
  jr nc,mc_nx
  inc h
  jr mc_nx
mc_scan:
  add a,a
  and 2
  ld (de),a
  push de
  ld b,32
mc_cell:
  ld a,(hl)
  rra
  jr nc,mc_z
  push bc
  push hl
  ld a,c
  add a,0B4h
  ld h,a
  add a,0Eh
  ld d,a
  ld a,32
  sub b
  add a,98h
  ld l,a
  ld e,a
  ld bc,32
  ld a,(hl)
  ld (de),a
  add hl,bc
  ex de,hl
  add hl,bc
  ex de,hl
  ld a,(hl)
  ld (de),a
  add hl,bc
  ex de,hl
  add hl,bc
  ex de,hl
  ld a,(hl)
  ld (de),a
  add hl,bc
  ex de,hl
  add hl,bc
  ex de,hl
  ld a,(hl)
  ld (de),a
  add hl,bc
  ex de,hl
  add hl,bc
  ex de,hl
  ld a,(hl)
  ld (de),a
  add hl,bc
  ex de,hl
  add hl,bc
  ex de,hl
  ld a,(hl)
  ld (de),a
  add hl,bc
  ex de,hl
  add hl,bc
  ex de,hl
  ld a,(hl)
  ld (de),a
  add hl,bc
  ex de,hl
  add hl,bc
  ex de,hl
  ld a,(hl)
  ld (de),a
  pop hl
  pop bc
  ld a,2
  jr mc_st
mc_z:
  xor a
mc_st:
  ld (hl),a
  inc hl
  djnz mc_cell
  pop de
mc_nx:
  inc de
  inc c
  ld a,c
  cp 14
  jr nz,mc_row
  ret

; ---------- 8587h: fin de fotograma del bucle principal ----------
MUPL:
  ld a,(FULLUP)
  or a
  jr z,mu_sel
  xor a
  ld (FULLUP),a
  call FULLUPL
  ld a,1
  ld (SYNC),a
  ret
mu_sel:
  ld hl,{DMAP}
  ld de,{ROWF}
  ld c,0
mu_row:
  ld a,(de)
  or a
  jr nz,mu_scan
  ld a,l
  add a,32
  ld l,a
  jr nc,mu_nx
  inc h
  jr mu_nx
mu_scan:
  push de
  ld b,32
mu_cell:
  ld a,(hl)
  or a
  jr z,mu_n
  push bc
  push hl
  ld a,32
  sub b
  ld l,a
  add a,a
  add a,a
  add a,a
  di
  out (99h),a
  ld a,c
  inc a
  or 40h
  out (99h),a
  ei
  ld a,c
  add a,0C2h
  ld h,a
  ld a,l
  add a,98h
  ld l,a
  ld de,32
  ld a,(hl)
  out (98h),a
  add hl,de
  ld a,(hl)
  out (98h),a
  add hl,de
  ld a,(hl)
  out (98h),a
  add hl,de
  ld a,(hl)
  out (98h),a
  add hl,de
  ld a,(hl)
  out (98h),a
  add hl,de
  ld a,(hl)
  out (98h),a
  add hl,de
  ld a,(hl)
  out (98h),a
  add hl,de
  ld a,(hl)
  out (98h),a
  pop hl
  pop bc
mu_n:
  inc hl
  djnz mu_cell
  pop de
mu_nx:
  inc de
  inc c
  ld a,c
  cp 14
  jr nz,mu_row
  ld a,(ROLL)
  inc a
  cp 14
  jr c,mu_r
  xor a
mu_r:
  ld (ROLL),a
  jp SPRUPL
"""
