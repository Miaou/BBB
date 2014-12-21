// Testing reliability of communication from external to local memory
//  using a pseudo random number generator.
// Let's try the Linear Congruential Generator, because we did the CRC the other day...

// PAB 2014

.origin 0

#include "latency.hp"

    // Configuration
    ENABLE_OCP
    MOV     r0, RAM_CTRREG_0|CTPPR_0
    MOV     r1, RAM_BOTH
    SBBO    r1, r0, 0, 4    // CONST_LOCAL=C28 points to the beginning of the SHARED memory (12KB == 0x3000)
    
    // Init (reads params)
    LBCO    r0, C28, 0, 8   // Number of iteration and first iteration
    MOV     r10, 1013904223 // Source : wiki (c in a*(X_n+c))
    MOV     r25, 0          // MAC mode will be multiply only
    MOV     r29, 1664525    // Source : wiki (a in a*(X_n+c))
    XOUT    0, r25, 1       // Set up MAC
    MOV     r3, 0           // Successful loops
    MOV     r1, 0           // X_0 is 0
    QBNE    NEXT_ITER, r0, 0
    MOV     r2, 0
    MOV     r4, 0
    SBCO    r0, C28, 0, 16  // ERROR (useless parameters)
    QBA     QUIT
    
    // Main loop
NEXT_ITER:
    LBCO    r2, C28, 4, 4   // Waits till number changed
    QBEQ    NEXT_ITER, r2, r1
    // Compute next number using X_n+1 = a*(X_n+c) mode 2**32
    ADD     r28, r1, r10
    MOV     r28, r28        // We have to wait! So that XIN copies the result of the new r28 with r29
    XIN     0, r25, 12      // r26 is X_n+1
    QBNE    after_if, r2, r26 // Does not count in r3 if result is not right...
    ADD     r3, r3, 1
  after_if:
    MOV     r1, r2
    SUB     r0, r0, 1
    SBCO    r0, C28, 0, 4
    QBNE    NEXT_ITER, r0, 0
    
    MOV     r4, r26         // Debug: output last X_n+1
    SBCO    r3, C28, 8, 8   // Outputs result
    //SBCO    r0, C28, 0, 16
    
// Cleaner
QUIT:
    // This is bogus and should be redone. (PRU0_ARM is 19, but should be 3,
    //  and +16 should be |32 (1<<5))
    MOV     r31.b0, PRU0_ARM_INTERRUPT+16 // It's done!
    HALT
