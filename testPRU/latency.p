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
    //MOV     r0, RAM_CTRREG_0|CTPPR_0
    //MOV     r1, RAM_BOTH
    //SBBO    r1, r0, 0, 4 // CONST_LOCAL will be RAM_CTRREG_0|CONTROL instead
    MOV     r1, RAM_BOTH
    LSL     r25, r1, 8 // R25 now points to the beginning of SHARED_MEMORY
    MOV     r0, RAM_CTRREG_0|CTPPR_0
    MOV     r1, (RAM_CTRREG_0|CONTROL)>>8
    SBBO    r1, r0, 0, 4 // C28 now points at the CONTROL flags of the PRU0. Seems more useful
    
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
    
    //MOV     r0, 0x05F5E100 // 100 000 000 * 10ns -> 1 sec
    MOV     r0, 0x00000100 // Low time.
  wait_latency_setup:
    // There should be a more "elegant" way with the cycle counter, but still requires 2 instructions in the loop...
    SUB     r0, r0, 1
    QBNE    wait_latency_setup, r0, 0
    
    // Switch menu
    LBBO    r0, r25, 0x20, 4
    QBEQ    OLDEST, r0, 0
    SUB     r0, r0, 1
    QBEQ    WAITER, r0, 0
    // default:
    JMP     QUIT

OLDEST:
    // Now the real deal, reset counter, sets output and waits
    // (counting with an ADD is ineffective because LBBO waits)
    MOV     r0, 0
    SBCO    r0, c28, 0x0C, 4  // Clears CYCLE count (C28 points to the PRU control flags)
    LBCO    r10, c28, 0x00, 1 // Takes lower byte of the CONTROL flag to set the COUNTER_ENABLE bit
    SET     r10.t3
    SBBO    r20, r5, 0, 4     // Sets the GPIO
    SBCO    r10, c28, 0x00, 1 // Cycle count is enabled
    LBBO    r21, r6, 0, 4     // Reads (and waits)
    
    LBCO    r0, C28, 0x0C, 4  // Reads the cycle count
    SBBO    r0, r25, 0x00, 4  // Stores the result in the shared memory

    // The same, with the falling edge.
    SBBO    r20, r4, 0, 4     // Clears the GPIO
    LBBO    r21, r6, 0, 4     // Reads (and waits)
    
    LBCO    r0, C28, 0x0C, 4  // Reads the cycle count
    SBBO    r0, r25, 0x04, 4  // Stores the result in the shared memory

    // Test Consecutive read to cycle count
    LBCO    r0, C28, 0x0C, 4
    SBBO    r0, r25, 0x08, 4  // Should be +2 since previous

    // Test Consecutive reads to cycle count
    LBCO    r0, C28, 0x0C, 4
    LBCO    r0, C28, 0x0C, 4
    SBBO    r0, r25, 0x0C, 4  // Should be +3 since previous
    
    // Test Consecutive reads to cycle count
    LBCO    r0, C28, 0x0C, 4
    LBCO    r0, C28, 0x0C, 4
    LBCO    r0, C28, 0x0C, 4
    SBBO    r0, r25, 0x10, 4  // Should be +4 since previous
    
    JMP     QUIT


WAITER:
    LBBO    r11, r25, 0x20, 8   // bContinue and wait period
    //SBBO    r12, r25, 0x00, 4
    QBNE    QUIT, r11, 1
    MOV     r13, r12
    MOV     r14, r12
    MOV     r15, r12

    SBBO    r20, r5, 0, 4   // Sets
  waiter_wait_0:
    SUB     r12, r12, 1
    QBNE    waiter_wait_0, r12, 0

    SBBO    r20, r4, 0, 4   // Clears
  waiter_wait_1:
    SUB     r13, r13, 1
    QBNE    waiter_wait_1, r13, 0

    SBBO    r20, r5, 0, 4   // Sets
  waiter_wait_2:
    SUB     r14, r14, 1
    QBNE    waiter_wait_2, r14, 0

    SBBO    r20, r4, 0, 4   // Clears
  waiter_wait_3:
    SUB     r15, r15, 1
    QBNE    waiter_wait_3, r15, 0

    JMP     WAITER


// Cleans after you
QUIT:
    // Makes GPIO back as input
    LBBO    r10, r2, 0, 4
    SET     r10.t31
    SBBO    r10, r2, 0, 4

    // Disable cycle count and clears it
    LBCO    r10, c28, 0x00, 1 // Takes lower byte of the CONTROL flag to clear the COUNTER_ENABLE bit
    CLR     r10.t3
    SBCO    r10, c28, 0x00, 1 
    MOV     r0, 0
    SBCO    r0, c28, 0x0C, 4  // Clears CYCLE count (C28 points to the PRU control flags)
    
    // Send notification to Host for program completion
    MOV     r31.b0, PRU0_ARM_INTERRUPT+16
    HALT
    
