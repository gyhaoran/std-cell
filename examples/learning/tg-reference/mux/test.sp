* EDU_MUX2: all eight (S, A, B) combinations
.include "/home/jasper/code/docs/std-cell/examples/learning/edu_inv.sp"
.include "/home/jasper/code/docs/std-cell/examples/learning/edu_tg.sp"
VDD VDD 0 1.8
VS S 0 PWL(0 0 3n 0 3.05n 0 6n 0 6.05n 0 9n 0 9.05n 0 12n 0 12.05n 1.8 15n 1.8 15.05n 1.8 18n 1.8 18.05n 1.8 21n 1.8 21.05n 1.8 24n 1.8)
VA A 0 PWL(0 0 3n 0 3.05n 0 6n 0 6.05n 1.8 9n 1.8 9.05n 1.8 12n 1.8 12.05n 0 15n 0 15.05n 0 18n 0 18.05n 1.8 21n 1.8 21.05n 1.8 24n 1.8)
VB B 0 PWL(0 0 3n 0 3.05n 1.8 6n 1.8 6.05n 0 9n 0 9.05n 1.8 12n 1.8 12.05n 0 15n 0 15.05n 1.8 18n 1.8 18.05n 0 21n 0 21.05n 1.8 24n 1.8)
XU A B S Z VDD 0 EDU_MUX2
CL Z 0 20f
.temp 25
.tran 5p 24n
.measure tran z_000 FIND v(z) AT=2n
.measure tran z_001 FIND v(z) AT=5n
.measure tran z_010 FIND v(z) AT=8n
.measure tran z_011 FIND v(z) AT=11n
.measure tran z_100 FIND v(z) AT=14n
.measure tran z_101 FIND v(z) AT=17n
.measure tran z_110 FIND v(z) AT=20n
.measure tran z_111 FIND v(z) AT=23n
.control
run
wrdata waveform.dat v(s) v(a) v(b) v(z)
quit
.endc
.end
