.origin 0
MOV     r0, 0x026004 // SYSCFG register in the CFG part of the momory
LBBO    r1, r0, 0, 1
CLR     r1.t4
SBBO    r1, r0, 0, 1 // Clears the STANDBY_INIT bit to enable the OCP master ports
MOV     r4, 0x44e07190
MOV     r20, 0
SET     r20.t31
SBBO    r20, r4, 0, 4 // Clears GPIO output
MOV     r31.b0, 0x23 // Interrupt
HALT
