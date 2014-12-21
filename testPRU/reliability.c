// Minimal PRU runner.
// Inspired from  https://github.com/beagleboard/am335x_pru_package/blob/master/pru_sw/example_apps/PRU_memAccessPRUDataRam/PRU_memAccessPRUDataRam.c
// PAB 2014


// Standard header files
#include <stdio.h>
// Driver header file
#include "prussdrv.h"
#include "pruss_intc_mapping.h"

#define PRU_NUM             0

int main(void)
{
    unsigned int ret;
    tpruss_intc_initdata pruss_intc_initdata = PRUSS_INTC_INITDATA;

    prussdrv_init (); /* Initialize the PRU */
    ret = prussdrv_open(PRU_EVTOUT_0); /* Open PRU Interrupt */
    if (ret)
    {
        printf("prussdrv_open failed\n");
        return ret;
    }
    prussdrv_pruintc_init(&pruss_intc_initdata); /* Get the interrupt initialized */
    printf("\tINFO: Executing example.\r\n"); /* Execute example on PRU */
    prussdrv_exec_program (PRU_NUM, "reliability.bin");
    printf("\tINFO: Waiting for interrupt.\r\n"); /* Wait until PRU_NUM has finished execution */
    prussdrv_pru_wait_event (PRU_EVTOUT_0);
    printf("\tINFO: Ok.\r\n");
    prussdrv_pru_clear_event (PRU_EVTOUT_0, PRU0_ARM_INTERRUPT);
    prussdrv_pru_disable(PRU_NUM); /* Disable PRU and close memory mapping*/
    prussdrv_exit ();
    return 0;
}

