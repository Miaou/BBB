# Testing PyPRUSS 3.2 btw...

import pypruss

if True:
    pypruss.init();
    pypruss.open(pypruss.PRU_EVTOUT_0)
    pypruss.pruintc_init();
    print('Loading program')
    pypruss.exec_program(0, '../../testPRU/minim-noInt.bin')
    pypruss.wait_for_event(pypruss.PRU_EVTOUT_0)
    print('Program finished')
    pypruss.clear_event(pypruss.PRU_EVTOUT_0, pypruss.PRU0_ARM_INTERRUPT)
    pypruss.pru_disable(0)
    pypruss.exit()
