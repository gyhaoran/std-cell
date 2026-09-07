EDU_INV teaching characterization
.include "/home/jasper/code/docs/std-cell/examples/learning/edu_inv.sp"
VDD VDD 0 1.8
VA A 0 PULSE(0 1.8 2n 133.333333333p 133.333333333p 8n 20n)
XU A Y VDD 0 EDU_INV
CL Y 0 50f
.tran 2p 18n
.measure tran cell_fall TRIG v(A) VAL=0.9 RISE=1 TARG v(Y) VAL=0.9 FALL=1
.measure tran cell_rise TRIG v(A) VAL=0.9 FALL=1 TARG v(Y) VAL=0.9 RISE=1
.measure tran rise_transition TRIG v(Y) VAL=0.36 RISE=1 TARG v(Y) VAL=1.44 RISE=1
.measure tran fall_transition TRIG v(Y) VAL=1.44 FALL=1 TARG v(Y) VAL=0.36 FALL=1
.measure tran input_slew TRIG v(A) VAL=0.36 RISE=1 TARG v(A) VAL=1.44 RISE=1
.control
run
wrdata waveform.dat v(A) v(Y)
quit
.endc
.end
