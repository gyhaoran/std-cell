* EDU_LATCH: transparent high, static feedback hold low
.include "/home/jasper/code/docs/std-cell/examples/learning/edu_inv.sp"
.include "/home/jasper/code/docs/std-cell/examples/learning/edu_tg.sp"
VDD VDD 0 1.8
VD D 0 PWL(0 0 2n 0 2.05n 1.8 8n 1.8 8.05n 0 14n 0)
VG G 0 PWL(0 1.8 5n 1.8 5.05n 0 11n 0 11.05n 1.8 14n 1.8)
XU D G Q VDD 0 EDU_LATCH
CL Q 0 20f
.temp 25
.tran 5p 14n
.measure tran q_initial FIND v(q) AT=1n
.measure tran q_follow FIND v(q) AT=4n
.measure tran q_hold_before FIND v(q) AT=7n
.measure tran q_hold_after FIND v(q) AT=10n
.measure tran q_reopen FIND v(q) AT=13n
.control
run
wrdata waveform.dat v(d) v(g) v(q)
quit
.endc
.end
