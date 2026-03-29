    section code,code
start_label:
    moveq #0,d0
    rts
    dx.l 2
    section data,data
data_label:
    dc.l start_label
    dx.l 1
