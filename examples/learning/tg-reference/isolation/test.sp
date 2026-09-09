* Off-state isolation: idealized storage versus explicit leakage
.include "/home/jasper/code/docs/std-cell/examples/learning/edu_inv.sp"
.include "/home/jasper/code/docs/std-cell/examples/learning/edu_tg.sp"
VDD VDD 0 1.8
VIN DIN 0 PWL(0 0 2n 0 2.05n 1.8 8n 1.8 8.05n 0 14n 0)
VEN EN 0 PWL(0 1.8 5n 1.8 5.05n 0 10n 0 10.05n 1.8 14n 1.8)
XI EN ENB VDD 0 EDU_INV
XF DIN YFLOAT EN ENB VDD 0 EDU_TG
XL DIN YLEAK EN ENB VDD 0 EDU_TG
CF YFLOAT 0 20f
CL YLEAK 0 20f
* Deliberate teaching leakage path; NOT a fitted MOS off-leakage model.
RLEAK YLEAK 0 1meg
.temp 25
.tran 5p 14n
.measure tran float_hold FIND v(yfloat) AT=9n
.measure tran leaky_hold FIND v(yleak) AT=9n
.measure tran float_reopen FIND v(yfloat) AT=12n
.measure tran leaky_reopen FIND v(yleak) AT=12n
.control
run
wrdata waveform.dat v(din) v(en) v(yfloat) v(yleak)
quit
.endc
.end
