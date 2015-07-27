// PRU part of the Servo lib.
// PAB, 2015

// 



#include "servos.hp"

.origin 0
.entrypoint CONFIG


// The given period should always be higher than this (this is not checked as of now)
#define FETCHING_WINDOW 200000


// Configuration of the PRU
CONFIG:
    CONFIGURE_C28 RAM_CTRREG_0
    ENABLE_OCP
    START_CYCLE_COUNT
    // Resets shared part of the RAM
    // Header is 12 bytes
    MOV     r0, RAM_BOTH|P_HEADER
    MOV     r1, N_SERVOS        // Max number of servos
    ZERO    &r2, S_HEADER       // Something like 12
    SBBO    r2, r0, 0, S_HEADER
    // Also, don't forget to clear header in FETCH zone
    MOV     r0, RAM_BOTH|P_HEADER|MASK_FETCH
    SBBO    r2, r0, 0, S_HEADER
    MOV     r0, RAM_BOTH|P_HEADER
    // Clears servos (optionnal, and not in FETCH)
    ADD     r0, r0, S_HEADER
    ZERO    &r2, S_SERVO        // Size of each servo
  clear_servo:
    SBBO    r2, r0, 0, S_SERVO  // Clears one servo data
    SUB     r1, r1, 1
    ADD     r0, r0, S_SERVO     // Next...
    QBNE    clear_servo, r1, 0  // ... while r1>0

// Main loop: comes back here after each PERIOD exactly
MAIN:
    RESET_CYCLE_COUNT_HOT r10   // Using r10 to reset the cycle count
    MOV     r0, RAM_BOTH|P_HEADER// r0 points to command (should be cleaner using C28)
    LBBO    r1, r0, 0, 12       // Loads r1=COMMAND, r2=nServo, and r3=nPeriod
    MOV     r4, FETCHING_WINDOW
    QBLT    FETCH_NEW_DATA, r4, r3 // When r3 < FETCHING_WINDOW, we must evade
    SUB     r3, r3, r4          // In a period, keep FETCHING_WINDOW cycles to FETCH_NEW_DATA
    // Parsing COMMAND
    QBEQ    START_DRIVING, r1, COMMAND_CONTINUE
    QBEQ    FETCH_NEW_DATA, r1, COMMAND_UPDATE // Should not happen here
    JMP     QUIT                // Quits on invalid command (or COMMAND_QUIT is cleaner)

START_DRIVING:
    LBCO    r4, c28, CTRREG_CYCLE, 4 // Reads time (time is supposed constant in an iteration)
    QBGE    FETCH_NEW_DATA, r3, r4  // Jumps when r4>=r3
    QBEQ    FETCH_NEW_DATA, r2, 0   // And jumps when there is not enough servos
    // (this jump is also taken when there are 0 configured servos, and period is 0)
    // (as there is no IDLE state)

    // Now sets the GPOs
    MOV     r5, RAM_BOTH|P_SERVOS // Beg of the servo data
    MOV     r10, r2             // r10 is loop variable, set to number of servos, decremented
  exec_servo:
    LBBO    r6, r5, 0, S_SERVO  // Reads r6=GPIO_reg_addr, r7=GPIO_bitmask, r8=nCycleCount
    QBGT    servo_set_low, r8, r4 // Jumps if r4>r8 (if t>nCycle)
    // Sets high
    MOV     r9, GPIO_SETDATAOUT
    JMP     servo_end
   servo_set_low:
    // Sets low
    MOV     r9, GPIO_CLEARDATAOUT
   servo_end:
    SBBO    r7, r6, r9, 4       // Set the bit of the *DATAOUT register of the GPIO ctrler at addr r6
    SUB     r10, r10, 1
    ADD     r5, r5, S_SERVO
    QBNE    exec_servo, r10, 0
    // Here, we have finished setting the signals for the servos.
    // CTRREG_CYCLE - r4 would give our resolution, and is a debug feature, as this would cost time...
    JMP START_DRIVING


FETCH_NEW_DATA:
    // Here, we are between the end of the period - FETCHING_WINDOW and the end of the period,
    //  it is time to see if new data should be written for the next round of signals.
    // We always have important masked time because the period is large compared to the length
    //  of the high-value signals...
    
    // So we go to the buffer zone of the memory to see if new data is given.
    // Sames adresses, but with maks MASK_FETCH
    MOV     r0, RAM_BOTH|MASK_FETCH|P_HEADER
    MOV     r10, r3             // Backup current period length
    MOV     r4, FETCHING_WINDOW
    ADD     r10, r10, r4        // Sets back to the real current period length, to finish fetch in time
    LBBO    r1, r0, 0, 12       // Loads r1=COMMAND, r2=nServo, and r3=nPeriod
    // Parsing new command
    QBEQ    fetch_finish_period, r1, FETCH_NO_CHANGE
    QBNE    QUIT, r1, FETCH_CHANGE

    // Here we are, with command FETCH_CHANGE, the write is supposedly finished by the host
    //  and we copy it to the control part of the memory
    // First copy the headers
    MOV     r11, RAM_BOTH|P_HEADER
    MOV     r1, COMMAND_CONTINUE// Clears the CHANGE state of the command, by the way...
    SBBO    r1, r11, 0, 12
    // Also clears the FETCH_CHANGE to FETCH_NOCHANGE in fetch zone
    MOV     r1, FETCH_NO_CHANGE
    SBBO    r1, r0, 0, 4

    // Now copy the servo data, and clear the GPO signal
    MOV     r5, RAM_BOTH|P_SERVOS
    MOV     r12, RAM_BOTH|MASK_FETCH|P_SERVOS
    MOV     r9, GPIO_CLEARDATAOUT // Register offset in the GPIO controller to ctr the value of the GPO
    MOV     r13, GPIO_OE        // Reg off in the GPIO controller to change the direction of the GPIO
  copy_servo:
    LBBO    r6, r12, 0, S_SERVO // Reads r6=GPIO_reg_addr, r7=GPIO_bitmask, r8=nCycleCount
    SBBO    r6, r5, 0, S_SERVO  // And put it back in its new place
    SBBO    r7, r6, r9, 4       // And clears set the GPO signal to low
    LBBO    r14, r6, r13, 4     // Get the current GPIO_OE register
    NOT     r7, r7              // Prepare to clear the bit: OE & (not mask)
    AND     r14, r14, r7
    SBBO    r14, r6, r13, 4     // And sets the GPIO to OUTPUT
    SUB     r2, r2, 1
    ADD     r5, r5, S_SERVO
    ADD     r12, r12, S_SERVO
    QBNE    copy_servo, r2, 0


    // Finally waits for the true end of the period
  fetch_finish_period:
    LBCO    r4, c28, CTRREG_CYCLE, 4 // Reads time
    SUB     r10, r10, r4        // r10 is now min(PERIOD,FETCHING_WINDOW)-currentTime
    LSR     r10, r10, 1         // r10 /= 2, as 2 instructions per wait loop
    SUB     r10, r10, 4         // Compensates these instructions (... can't be measured anyway)
   fetch_finish_wait:
    SUB     r10, r10, 1
    QBNE    fetch_finish_wait, r10, 0 // registers are unsigned, so compare only to 0
    
    // Here we are, at PERIOD or PERIOD-1 cycle
    JMP     MAIN


QUIT:
    SIGNAL_AND_HALT





