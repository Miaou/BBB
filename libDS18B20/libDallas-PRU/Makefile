# No cross-compile.
# PAB 2014, built from a test project



PATH_PRU_SW=./am335x_pru_package/pru_sw/
PATH_PRU_LOADER=$(PATH_PRU_SW)app_loader/
PATH_PYPRUSS=./pypruss/pypruss
MODE=not_release
BUILD_LIB=yes

ifeq ($(MODE),release)
    MODE_CFLAGS=-O3 -g0
    MODE_LDFLAGS=-s
else
    MODE_CFLAGS=-g -Wall
    MODE_LDFLAGS=
endif



CC=gcc
PASM=$(PATH_PRU_SW)utils/pasm
ifeq ($(BUILD_LIB),yes)
    CFLAGS=$(MODE_CFLAGS) -I$(PATH_PRU_LOADER)include/ -I./ -fPIC -fvisibility=hidden -L$(PATH_PRU_LOADER)lib/
    LDFLAGS=$(MODE_LDFLAGS) -L$(PATH_PRU_LOADER)lib/ -shared
    LIB_STA=-lprussdrv
    LIB_DYN=
else
    CFLAGS=$(MODE_CFLAGS) -I$(PATH_PRU_LOADER)include/ -I./ -L$(PATH_PRU_LOADER)lib/
    LDFLAGS=$(MODE_LDFLAGS) -L$(PATH_PRU_LOADER)lib/
    LIB_STA=
    LIB_DYN=-lprussdrv
endif
SRC=
OBJ=$(SRC:%.c=%.o)
#SRCP=$(SRC:%.c=%.p)
SRCP=dallas.p
OLIB=libDallasPRU.so
OUT=
BIN=$(SRCP:%.p=%.bin)



.PHONY: all clean cleannolib

all: precompile $(OBJ) $(OUT) $(BIN)

cleannobin:
	rm -f $(OBJ)
clean: cleannobin
	rm -f $(OUT)
#	rm -f $(OLIB)
	rm -f $(BIN)
#	make -C$(PATH_PRU_SW) clean
	make -C$(PATH_PYPRUSS) clean

precompile: $(PATH_PRU_LOADER)lib/libprussdrv.so $(PASM) pypruss.so
$(PATH_PRU_LOADER)lib/libprussdrv.so:
	make -C$(PATH_PRU_SW)
$(PASM):
	make -C$(PATH_PRU_SW)
pypruss.so:
	make -C$(PATH_PYPRUSS)

$(OUT): $(OBJ)
	$(CC) $(LDFLAGS) $(LIB_DYN) $@.o -o $@ $(LIB_STA)
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

%.bin: %.p
	$(PASM) -V3 -b $<


