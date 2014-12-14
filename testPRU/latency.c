// Inspired from  https://github.com/beagleboard/am335x_pru_package/blob/master/pru_sw/example_apps/PRU_memAccessPRUDataRam/PRU_memAccessPRUDataRam.c
// PAB 2014


// Standard header files
#include <stdio.h>
#include <sys/mman.h>
#include <fcntl.h>
/*#include <errno.h>
#include <unistd.h>
#include <string.h>*/

// Driver header file
#include "prussdrv.h"
#include "pruss_intc_mapping.h"


#define PRU_NUM             0
#define PRU_SHARED_OFFSET   0x00010000  
#define PRUICSS_MEM_SIZE    0x00080000


int print_shared_mem(void);

// I don't like the way it is coded, but I don't have any better for now.
int main(void)
{
    unsigned int ret;
    tpruss_intc_initdata pruss_intc_initdata = PRUSS_INTC_INITDATA;

    /* Initialize the PRU */
    prussdrv_init ();

    /* Open PRU Interrupt */
    ret = prussdrv_open(PRU_EVTOUT_0);
    if (ret)
    {
        printf("prussdrv_open failed\n Did you set the PRU in the device tree?\n echo BB-BONE-PRU > /sys/devices/bone_capemgr.9/slots\n");
        return ret;
    }

    /* Get the interrupt initialized */
    prussdrv_pruintc_init(&pruss_intc_initdata);

    /* Initialize example 
    printf("\tINFO: Initializing example.\r\n");
    LOCAL_exampleInit(PRU_NUM); */

    /* Execute example on PRU */
    printf("\tINFO: Executing example.\r\n");
    prussdrv_exec_program (PRU_NUM, "./latency.bin");

    /* Wait until PRU_NUM has finished execution */
    printf("\tINFO: Waiting for HALT command.\r\n");
    prussdrv_pru_wait_event (PRU_EVTOUT_0);
    printf("\tINFO: PRU completed transfer (meaning???).\r\n");
    prussdrv_pru_clear_event (PRU_EVTOUT_0, PRU0_ARM_INTERRUPT);
    
    /* Observe results */
    ret = print_shared_mem();
    if(ret)
        printf("Reading shared memory failed with error %i\n", ret);

    /* Disable PRU and close memory mapping*/
    prussdrv_pru_disable(PRU_NUM);
    prussdrv_exit ();
    //munmap(ddrMem, 0x0FFFFFFF); // No, you are not responsible for this...
    //close(mem_fd);

    return 0;
}


int print_shared_mem(void)
{
    unsigned int *lData; // Of len 2
    unsigned int i;
    FILE *pruDescr;
    int mem_fd;
    void *pruMem;
    int *pruMemAddr;
    
    // Finding where PRU-ICSS memory is
    pruDescr = fopen("/sys/class/uio/uio0/maps/map0/addr", "r");
    if(! pruDescr)
        return -1;
    
    if(fscanf("0x%X", &pruMemAddr) < 1)
        return -2;
    fclose(pruDescr);
    
    // Mapping PRU memory to access it
    mem_fd = open("/dev/mem", O_RDONLY);
    if(mem_fd < 0)
        return -3;
    
    pruMem = mmap(0, PRUICSS_MEM_SIZE, PROT_WRITE | PROT_READ, MAP_SHARED, mem_fd, pruMemAddr);
    if(! pruMem)
    {
        close(mem_fd);
        return -4;
    }
    
    // Accessing Shared mem
    lData = *(unsigned int *)(pruMem + PRU_SHARED_OFFSET);
    printf("Latency results:\n-> set: %u cycles\n -> clr: %u cycles\n", lData[0], lData[1]);
    
    // Cleaning after self
    munmap(pruMem, PRUICSS_MEM_SIZE);
    close(mem_fd);
    return 0;
}


