// PRU part of the Dallas' lib
// PAB, 2014

// COMPLETE ME

// I used an action chain.
// Pros: low-level, easy to implement
// Cons: multi-action timings are tricky


#include "dallas.hp"


.entrypoint CONFIG

// Configuration
CONFIG:
    CONFIGURE_C28   RAM_SHARED
    ENABLE_OCP
    // Resets COMMAND
    ZERO    r0, 4
    SBCO    r0, C28, 0, 4
    // Resets actions
    MOV     r0, P_ACTION
    MOV     r1, N_ACTION
    ZERO    r2, S_ACTION
    SBCO    r2, r0, 0, 4    // Clears number of actions
    ADD     r0, r0, 4
  clear_action:
    SBCO    r2, r0, 0, S_ACTION // Clears one action
    SUB     r1, r1, 1
    ADD     r0, r0, S_ACTION    // Goes to next action
    QBNE    clear_action, r1, 0

// Main switch
MAIN:
    LBCO    r0, C28, 0, 4
    QBEQ    MAIN, r0, NO_COMMAND
    // Parse action tree
    MOV     r1, 0x100       // Action offset
    LBCO    r2, C28, r1, 4  // Number of remaining actions (should be below N_ACTION)
    ADD     r1, r1, 4
  switch_action:
    LBCO    r3, C28, r1, 12 // r3=Action, r4=GPIO base, r5=GPIO mask
    // r1 must points to current location, so that GET can work)
    QBEQ    SET_DIR_OUT, r3, CMD_SET_DIR_OUT
    QBEQ    SET_DIR_IN, r3, CMD_SET_DIR_IN
    QBEQ    SET_LOW, r3, CMD_SET_LOW
    QBEQ    SET_HIGH, r3, CMD_SET_HIGH
    QBEQ    GET, r3, CMD_GET
    QBEQ    WAIT, r3, CMD_WAIT
    QBA     QUIT
  post_action:
    ADD     r1, r1, 12      // Points to next action
    SUB     r2, r2, 1
    QBNE    switch_action, r2, 0 // While there is still an action to read
    SBCO    r2, C28, 0, 4   // No more command: it was just completed
    MOV     r31.b0, INTERRUPT_VALID | PRU0_ARM_INTERRUPT // Tells ARM action chain is treated
    QBA     MAIN            // Wait until next action

// Elementary functions
SET_DIR_OUT:
    MOV     r7, GPIO_OE     // Corresponding bit must be cleared to have an output
    LBBO    r6, r4, r7, 4   // Current value of GPIO_OE
    NOT     r5, r5          // AND (NOT mask) to clear the bit
    AND     r6, r6, r5
    SBBO    r6, r4, r7, 4   // Set the new GPIO_OE
    QBA     post_action
SET_DIR_IN:
    MOV     r7, GPIO_OE     // Corresponding bit must be set to have an input
    LBBO    r6, r4, r7, 4   // Current value of GPIO_OE
    OR      r6, r6, r5      // OR mask to set the bit
    SBBO    r6, r4, r7, 4   // Set the new GPIO_OE
    QBA     post_action
SET_LOW:
    MOV     r7, GPIO_CLEARDATAOUT
    SBBO    r5, r4, r7      // Just set the bit in the CLEARDATAOUT register
    QBA     post_action
SET_HIGH:
    MOV     r7, GPIO_SETDATAOUT
    SBBO    r5, r4, r7      // Just set the bit in the SETDATAOUT register
    QBA     post_action
GET:
    MOV     r7, GPIO_DATAIN // Corresponding bit is the value
    LBBO    r6, r4, r7, 4   // Get DATAIN
    AND     r6, r6, r5      // Now, if value, r6 is not null
    SBCO    r6, r1, 4, 4    // Writes instead of action.GPIO_base. Can test multiple bits at once...
    QBA     post_action
WAIT:
    QBLT    post_action, r4, 10 // WAIT cannot be accurate between 0 and 90 nanosec
    SUB     r4, r4, 9       // Compensate previous commands and this one
  wait_sub:
    SUB     r4, r4, 1       // Counts down
    QBNE    wait_sub, r4, 0
    QBA     post_action


// Quit'n'clean
QUIT:
    // Makes GPIO back to input (safer)
    // No, you can't.

    // Disable cycle count and clears it
    LBCO    r7, c4, CTRREG_CONTROL, 1 // Takes lower byte of the CONTROL flag to clear the COUNTER_ENABLE bit
    CLR     r7.t3
    SBCO    r7, c4, CTRREG_CONTROL, 1 
    MOV     r7, 0
    SBCO    r7, c4, CTRREG_CYCLE, 4   // Clears CYCLE count
    
    
    MOV     r31.b0, INTC_VALID_STROBE | PRU0_ARM_INTERRUPT // Send notification to Host
    HALT
