# No Cross compile.


PATH_PRU_SW=../libDS18B20/libDallas-PRU/am335x_pru_package/pru_sw/
PATH_PRU_LOADER=$(PATH_PRU_SW)app_loader/

ifeq ($(MODE),release)
    MODE_CFLAGS=-O3 -g0
    MODE_LDFLAGS=-s
else
    MODE_CFLAGS=-g -Wall
    MODE_LDFLAGS=
endif



CC=gcc
PASM=$(PATH_PRU_SW)utils/pasm
CFLAGS=$(MODE_CFLAGS) -I$(PATH_PRU_LOADER)include/ -I./ -fPIC -fvisibility=hidden -L$(PATH_PRU_LOADER)lib/
#LDFLAGS=$(MODE_LDFLAGS) -L$(PATH_PRU_LOADER)lib/ -shared
LDFLAGS=$(MODE_LDFLAGS) -L$(PATH_PRU_LOADER)lib/
#LIB_STA=-lprussdrv
LIB_STA=
LIB_DYN=-lprussdrv
SRC=latency.c
OBJ=$(SRC:%.c=%.o)
SRCP=latency.p
#OLIB=libDallas.so
OUT=latency
BIN=latency.bin



.PHONY: all clean cleannolib

all: precompile $(OBJ) $(OUT) $(BIN)

cleannobin:
	rm -f $(OBJ)
clean: cleannobin
	rm -f $(OUT)
#	rm -f $(OLIB)
	rm -f $(BIN)

precompile: $(PATH_PRU_LOADER)lib/libprussdrv.so $(PASM)
$(PATH_PRU_LOADER)lib/libprussdrv.so:
	make -C$(PATH_PRU_SW)
$(PASM):
	make -C$(PATH_PRU_SW)

$(OUT): $(OBJ)
	$(CC) $(LDFLAGS) $(LIB_DYN) $(OBJ) -o $@ $(LIB_STA)
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

$(BIN): $(SRCP)
	$(PASM) -V3 -b $(SRCP)