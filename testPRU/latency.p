// Inspired from https://github.com/beagleboard/am335x_pru_package/blob/master/pru_sw/example_apps/PRU_memAccessPRUDataRam/PRU_memAccessPRUDataRam.p
// PAB 2014
// cf latency.hp

// Some defines in latency.hp are a JOKE. For instance, CONST_LOCAL is a
//  customizable constant (C28) which is bound to point to a local location.
//  It is not constant, and you must know lots more than its name to use it.
//  AND I am not sure it is clearer to write CONST_LOCAL instead of C28.


.origin 0
.entrypoint LATENCY_TEST

#include "latency.hp"


LATENCY_TEST:

    // Customize the constant CONST_LOCAL by changing the "block index register"
    // for PRU0 by setting (RAM_CTRREG+CTPPR_0).w0 which maps to c28_pointer[15:0]
    // This will make C28 point to shared memory. (C29 is set by the way, but we dont care)
    MOV     r0, RAM_CTRREG_0|CTPPR_0
    MOV     r1, RAM_BOTH
    SBBO    r1, r0, 0, 4

    
// Writes to SET/CLEARDATAOUT on P9_13, waits for an answer
LATENCY_SYNC:
    //MOV     r1, GPIO0
    // It has to be 2 instructions... or serious hacks.
    MOV     r2, GPIO0 | GPIO_OE
    MOV     r3, GPIO0 | GPIO_DATAIN
    MOV     r4, GPIO0 | GPIO_CLEARDATAOUT
    MOV     r5, GPIO0 | GPIO_SETDATAOUT
    MOV     r6, GPIO0 | GPIO_DATAOUT
    
    // Clear the bit of GPIO_OE register, to set GPIO as O
    LBBO    r10, r2, 0, 4
    CLR     r10.t31 // This is a joke. This should have a #define, because 31st bit is the bit corresponding to gpio0_31, that is to say, P9_13... Not obvious.
    SBBO    r10, r2, 0, 4
    
    // Clears output
    MOV     r20, 0
    SET     r20.t31
    SBBO    r20, r4, 0, 4
    
    MOV     r0, 0x05F5E100 // 100 000 000 * 10ns -> 1 sec
  wait_latency_setup:
    // There should be a more "elegant" way with the cycle counter, but still requires 2 instructions in the loop...
    SUB     r0, r0, 1
    QBNE    wait_latency_setup, r0, 0
    
    // Now the real deal, sets output and counts
    SBBO    r20, r5, 0, 4
  wait_latency_set_response:
    // This should use the cycle counter as Global-Mem IOs cant be 1-cycle long
    ADD     r0, r0, 1
    LBBO    r21, r6, 0, 4
    QBBC    wait_latency_set_response, r21.t31
    // Writes the result in Shared Memory
    SBCO    r0, CONST_LOCAL, 0, 4

    
    //Clears output and counts
    MOV     r0, 0
    SBBO    r20, r4, 0, 4
  wait_latency_clr_response:
    // This should use the cycle counter as Global-Mem IOs cant be 1-cycle long
    ADD     r0, r0, 1
    LBBO    r21, r6, 0, 4
    QBBS    wait_latency_clr_response, r21.t31
    // Writes the result in Shared Memory
    SBCO    r0, CONST_LOCAL, 4, 4
    
    JMP     QUIT

// Cleans after you
QUIT:
    // Makes GPIO back as input
    LBBO    r10, r2, 0, 4
    SET     r10.t31
    SBBO    r10, r2, 0, 4
    
    // Send notification to Host for program completion
    MOV     r31.b0, PRU0_ARM_INTERRUPT+16
    HALT
    
