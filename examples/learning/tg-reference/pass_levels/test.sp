* Single MOS versus CMOS transmission gate
.include "/home/jasper/code/docs/std-cell/examples/learning/edu_inv.sp"
.include "/home/jasper/code/docs/std-cell/examples/learning/edu_tg.sp"
VDD VDD 0 1.8
VIN DIN 0 PULSE(0 1.8 2n 50p 50p 6n 20n)
MN YN VDD DIN 0 N_EDU W=1u L=0.18u
MP YP 0 DIN VDD P_EDU W=2u L=0.18u
XT DIN YTG VDD 0 VDD 0 EDU_TG
* Reverse test: drive the second signal port, observe the first.
XR YREV DIN VDD 0 VDD 0 EDU_TG
CN YN 0 20f
CP YP 0 20f
CT YTG 0 20f
CR YREV 0 20f
.temp 25
.tran 5p 14n
.measure tran n_high FIND v(yn) AT=7n
.measure tran p_high FIND v(yp) AT=7n
.measure tran tg_high FIND v(ytg) AT=7n
.measure tran rev_high FIND v(yrev) AT=7n
.measure tran n_low FIND v(yn) AT=13n
.measure tran p_low FIND v(yp) AT=13n
.measure tran tg_low FIND v(ytg) AT=13n
.measure tran rev_low FIND v(yrev) AT=13n
.control
run
wrdata waveform.dat v(din) v(yn) v(yp) v(ytg) v(yrev)
quit
.endc
.end
