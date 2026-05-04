# ORG code ranges

TODO: Checked and update this document for lacking detail or incorrectness.

The goal of reversing a target is to obtain the code and data in a form that the
user will be able to use like the original developers. This will use a
combination of analysis and rendering to produce that reformalised code and
data.

Where this relates to ORG code ranges is that some of these targets will be
assembled to a fixed address. They require both being loaded at that address and
entered at an address within the range of the occupied memory range. It is not
guaranteed that the entrypoint will be the base address.

## ORG usage nuances

A label reference from before the ORG section will be converted to the relevant
absolute address within the ORG section. Here `local_payload_START` stays a
local PC-relative reference to the current segment's data. `absolute_START` is
replaced by it's ORG value, in this case $400.

```
	lea.l local_payload_START(pc),a6
local_bootstrap:
	move.l #absolute_END-absolute_START,d0
	lea.l absolute_START.l,a0
loc_0_00000046:
	move.b (a6)+,(a0)+
	subq.l #1,d0
	bcc.b loc_0_00000046

	jmp absolute_START.l
	dc.b $00,$00
local_payload_START:
    ORG $400
absolute_START:
	move.w #INTF_CLRALL,_custom+intena.l
  ....
absolute_END
```

It is not possible to use multiple ORG sections to reflect multiple ranges of
the segment copied to different absolute memory ranges, unless the original
code supports that. We are not rewriting the code we are reversing, we are
instead amending it to be rendered in original form. So while we can add an
`ORG $90` in addition to the `ORG $400` the assembler can and will get
confused and modify cross ORG references. There is an implicit requirement
that we only use an ORG section for the remainder of the segment. 

```
	lea.l local_bootstrap(pc),a0
	lea.l $00000090.l,a1
	moveq.l #40,d0
copy_trap0:
	move.b (a0)+,(a1)+
	dbf.w d0,copy_trap0

	lea.l local_payload_START(pc),a6
	move.l #$90,$80.l ; Trap 0 instruction vector
	trap #0

local_bootstrap:
	move.l #absolute_END-absolute_START,d0
	lea.l absolute_START.l,a0
loc_0_00000046:
	move.b (a6)+,(a0)+
	subq.l #1,d0
	bcc.b loc_0_00000046

	jmp absolute_START.l
	dc.b $00,$00
local_payload_START:
    ORG $400
absolute_START:
	move.w #INTF_CLRALL,_custom+intena.l
  ....
absolute_END
```
