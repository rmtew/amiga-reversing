    section code,code
start_label:
    moveq #0,d0
    rts
    section data_c,data,chip
data_label:
    dc.l start_label
    section bss_f,bss,fast
bss_label:
    ds.b 8
