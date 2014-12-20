.origin 0
MOV     r4, 0x44e07190
MOV     r20, 0
SET     r20.t31
SBBO    r20, r4, 0, 4 // Clears GPIO output
MOV     r31.b0, 0x23 // Interrupt
HALT
