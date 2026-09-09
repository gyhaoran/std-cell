* Tutorial-only planar CMOS circuits. Not a foundry/FreePDK45 model.
* The test deck must include edu_inv.sp first (N_EDU/P_EDU and EDU_INV).
* All MOS instances use D G S B order; all data stay in [VSS,VDD].
.subckt EDU_TG X Y EN ENB VDD VSS
MN Y EN  X VSS N_EDU W=1u L=0.18u
MP Y ENB X VDD P_EDU W=2u L=0.18u
.ends EDU_TG

* Noninverting 2:1 MUX: S=0 selects A, S=1 selects B. Six MOS total.
.subckt EDU_MUX2 A B S Z VDD VSS
XSEL S SN VDD VSS EDU_INV
XA A Z SN S VDD VSS EDU_TG
XB B Z S SN VDD VSS EDU_TG
.ends EDU_MUX2

* Positive-level static latch. Ten MOS including the G inverter.
* G=1: input enabled, feedback disabled. G=0: feedback enabled.
.subckt EDU_LATCH D G Q VDD VSS
XEN G GB VDD VSS EDU_INV
XIN D N G GB VDD VSS EDU_TG
XI1 N QN VDD VSS EDU_INV
XI2 QN Q VDD VSS EDU_INV
XFB Q N GB G VDD VSS EDU_TG
.ends EDU_LATCH
