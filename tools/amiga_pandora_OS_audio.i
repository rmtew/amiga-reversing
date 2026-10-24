; audio.device ownership before direct Paula access. No channel stealing:
; OpenDevice requests all four at minimum precedence; fail if unavailable.
; NDK IOAudio/MsgPort definitions own every field; private reply port.
; Protocol reference: https://wiki.amigaos.net/wiki/Audio_Device
; ADCMD_FREE completes the outstanding LOCK before WaitIO/CloseDevice.
acquire_audio:
    movea.l 4.w,a6
    moveq #-1,d0
    jsr _LVOAllocSignal(a6)
    move.l d0,state_signal-host_state(a5)
    cmpi.l #-1,d0
    beq.w audio_failed
    lea state_audio_port-host_state(a5),a0
    move.b #NT_MSGPORT,LN_TYPE(a0)
    move.b d0,MP_SIGBIT(a0)
    clr.b MP_FLAGS(a0)
    suba.l a1,a1
    jsr _LVOFindTask(a6)
    lea state_audio_port-host_state(a5),a0
    move.l d0,MP_SIGTASK(a0)
    lea MP_MSGLIST(a0),a1
    lea LH_TAIL(a1),a2
    move.l a2,LH_HEAD(a1)
    clr.l LH_TAIL(a1)
    move.l a1,LH_TAILPRED(a1)
    lea state_audio_request-host_state(a5),a1
    move.b #NT_MESSAGE,LN_TYPE(a1)
    move.b #ADALLOC_MINPREC,LN_PRI(a1)
    move.l a0,MN_REPLYPORT(a1)
    move.w #ioa_SIZEOF,MN_LENGTH(a1)
    move.b #IOF_QUICK|ADIOF_NOWAIT,IO_FLAGS(a1)
    clr.w ioa_AllocKey(a1)
    lea audio_channel_mask(pc),a0
    move.l a0,ioa_Data(a1)
    move.l #1,ioa_Length(a1)
    lea audio_name(pc),a0
    moveq #0,d0
    moveq #0,d1
    jsr _LVOOpenDevice(a6)
    tst.l d0
    bne.w audio_failed
    move.l #1,state_audio_open-host_state(a5)
    lea state_audio_request-host_state(a5),a1
    move.l IO_UNIT(a1),d0
    andi.l #15,d0
    cmpi.l #15,d0
    bne.b audio_failed
    move.b #ADALLOC_MAXPREC,LN_PRI(a1)
    move.w #ADCMD_SETPREC,IO_COMMAND(a1)
    jsr _LVODoIO(a6)
    tst.b d0
    bne.b audio_failed
    lea state_audio_request-host_state(a5),a0
    lea state_audio_lock_request-host_state(a5),a1
    move.w #ioa_SIZEOF-1,d0
copy_lock_request:
    move.b (a0)+,(a1)+
    dbra d0,copy_lock_request
    lea state_audio_lock_request-host_state(a5),a1
    move.w #ADCMD_LOCK,IO_COMMAND(a1)
    clr.b IO_FLAGS(a1)
    jsr _LVOSendIO(a6)
    move.l #1,state_audio_lock-host_state(a5)
    lea state_audio_lock_request-host_state(a5),a1
    jsr _LVOCheckIO(a6)
    tst.l d0
    bne.b audio_failed
    moveq #1,d0
    rts
audio_failed:
    moveq #0,d0
    rts
release_audio:
    movea.l 4.w,a6
    tst.l state_audio_open-host_state(a5)
    beq.b release_signal
    lea state_audio_request-host_state(a5),a1
    move.w #ADCMD_FREE,IO_COMMAND(a1)
    jsr _LVODoIO(a6)
    tst.l state_audio_lock-host_state(a5)
    beq.b close_audio
    lea state_audio_lock_request-host_state(a5),a1
    jsr _LVOWaitIO(a6)
    clr.l state_audio_lock-host_state(a5)
close_audio:
    lea state_audio_request-host_state(a5),a1
    jsr _LVOCloseDevice(a6)
    clr.l state_audio_open-host_state(a5)
release_signal:
    move.l state_signal-host_state(a5),d0
    cmpi.l #-1,d0
    beq.b audio_released
    jsr _LVOFreeSignal(a6)
    move.l #-1,state_signal-host_state(a5)
audio_released:
    rts
audio_name: dc.b "audio.device",0
audio_channel_mask: dc.b 15
    even
