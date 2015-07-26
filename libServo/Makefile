# Compiles the tools in some other directory,
#  then compiles the pru assembly.
# No Cross compile.
# Depends on:
#  - PRU Loader lib (libprussdrv)
#  - PRU assembler
#  - pypruss package (to use the loader with Python3)

# PAB 2015


PATH_PRU_SW=../libDS18B20/libDallas-PRU/am335x_pru_package/pru_sw/
PATH_PYPRUSS=../libDS18B20/libDallas-PRU/pypruss/pypruss/
PATH_PRU_LOADER=$(PATH_PRU_SW)app_loader/
MODE=not_release
BUILD_PRULIB_AS_STATIC=yes

ifeq ($(MODE),release)
    MODE_CFLAGS=-O3 -g0
    MODE_LDFLAGS=-s
else
    MODE_CFLAGS=-g -Wall
    MODE_LDFLAGS=
endif



CC=gcc
PASM=$(PATH_PRU_SW)utils/pasm
ifeq ($(BUILD_PRULIB_AS_STATIC),yes)
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
SRCP=servos.p
BIN=$(SRCP:%.p=%.bin)
OLIB=
OUT=



.PHONY: all clean cleannolib

all: precompile $(OBJ) $(OUT) $(BIN)

cleannobin:
	rm -f $(OBJ)
clean: cleannobin
	rm -f $(OUT)
	rm -f $(OLIB)
	rm -f $(BIN)
	#make -C$(PATH_PRU_SW) clean
	make -C$(PATH_PYPRUSS) clean
	rm pypruss.so


# Compile libs and assembler, if needed.
precompile: $(PATH_PRU_LOADER)lib/libprussdrv.so $(PASM) pypruss.so
$(PATH_PRU_LOADER)lib/libprussdrv.so:
	make -C$(PATH_PRU_SW)../ all
$(PASM):
	make -C$(PATH_PRU_SW)../ all
pypruss.so:
	make -C$(PATH_PYPRUSS)
	cp $(PATH_PYPRUSS)../../pypruss.so .


# Compiles C, if needed (but now that there is pypruss, ...)
$(OUT): $(OBJ)
	$(CC) $(LDFLAGS) $(LIB_DYN) $@.o -o $@ $(LIB_STA)
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# Compiles the PRU assemblies
%.bin: %.p
	$(PASM) -V3 -b $<




