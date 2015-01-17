// PRU part of the Dallas' lib
// PAB, 2014

// COMPLETE ME

// I used an action chain.
// Pros: low-level, easy to implement
// Cons: multi-action timings are tricky


#include "dallas.hp"


.origin 0
.entrypoint CONFIG

// Configuration
CONFIG:
    CONFIGURE_C28   RAM_BOTH
    ENABLE_OCP
    // Resets COMMAND
    ZERO    &r0, 4
    SBCO    r0, C28, 0, 4
    // Resets actions
    MOV     r0, RAM_BOTH|P_ACTION
    MOV     r1, N_ACTION
    ZERO    &r2, S_ACTION
    SBBO    r2, r0, 0, 4    // Clears number of actions
    ADD     r0, r0, 4
  clear_action:
    SBBO    r2, r0, 0, S_ACTION // Clears one action
    SUB     r1, r1, 1
    ADD     r0, r0, S_ACTION    // Goes to next action
    QBNE    clear_action, r1, 0

// Main switch
MAIN:
    LBCO    r0, C28, 0, 4   // Should be COMMAND_START, and is set to WOMMAND_WORKING while working
    // Parsing command
    QBEQ    MAIN, r0, COMMAND_STDBY
    QBEQ    QUIT, r0, COMMAND_BYE
    MOV     r1, COMMAND_STDBY
    SBCO    r1, C28, 0, 4
    QBEQ    MAIN, r0, COMMAND_WORKING
    MOV     r1, COMMAND_WORKING
    SBCO    r1, C28, 0, 4
    QBNE    MAIN, r0, COMMAND_START
    // Parse action tree
    MOV     r1, P_ACTION    // Action offset
    LBCO    r2, C28, r1, 4  // Number of remaining actions (should be below N_ACTION)
    ADD     r1, r1, 4
  switch_action:
    LBCO    r3, C28, r1, 12 // r3=Action, r4=GPIO base, r5=GPIO mask
    // r1 must points to current location, so that GET can work
    // r1,r2 must not be altered, so that post_action can work
    QBEQ    SET_DIR_OUT, r3, ACT_SET_DIR_OUT
    QBEQ    SET_DIR_IN, r3, ACT_SET_DIR_IN
    QBEQ    SET_LOW, r3, ACT_SET_LOW
    QBEQ    SET_HIGH, r3, ACT_SET_HIGH
    QBEQ    GET, r3, ACT_GET
    QBEQ    WAIT, r3, ACT_WAIT
    SBCO    r3, C28, 0, 4
    QBA     QUIT
  post_action:
    ADD     r1, r1, 12      // Points to next action
    SUB     r2, r2, 1
    QBNE    switch_action, r2, 0 // While there is still an action to read
    SBCO    r2, C28, 0, 4   // No more command: it was just completed (r2 == COMMAND_STDBY == 0)
    MOV     r1, P_ACTION
    SBCO    r2, C28, r1, 4  // Resets nAction too
    MOV     r31.b0, INTC_VALID_STROBE | PRU0_ARM_INTERRUPT // Tells ARM action chain is treated
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
    SBBO    r5, r4, r7, 4   // Just set the bit in the CLEARDATAOUT register
    QBA     post_action
SET_HIGH:
    MOV     r7, GPIO_SETDATAOUT
    SBBO    r5, r4, r7, 4   // Just set the bit in the SETDATAOUT register
    QBA     post_action
GET:
    MOV     r7, GPIO_DATAIN // Corresponding bit is the value
    LBBO    r6, r4, r7, 4   // Get DATAIN
    AND     r4, r6, r5      // Now, if value, r4 is not null
    SBCO    r3, C28, r1, 8  // Writes back r3=Action, r4=not null if readbit. Can test multiple bits at once...
    QBA     post_action
WAIT:
    QBGT    post_action, r4, 10 // WAIT cannot be accurate between 0 and 90 nanosec
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
