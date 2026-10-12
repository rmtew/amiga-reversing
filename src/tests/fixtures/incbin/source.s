 SECTION assets,data
first:
 INCBIN "assets/first.bin"
interior:
 INCBIN "assets/empty.bin"
 INCBIN 'assets/second, odd.bin'
 dc.l interior
 dc.w interior-first
 even
 dc.w $abcd
