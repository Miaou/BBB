# Quand on attaque un Makefile, on est toujours aussi emmerdé...


PATH_BBBIO=./libBBBIO/
#MODE=release

ifeq ($(MODE),release)
    MODE_CFLAGS=-O3 -g0
    MODE_LDFLAGS=-s
else
    MODE_CFLAGS=-Wall
    MODE_LDFLAGS=
endif



CC=gcc
CFLAGS=$(MODE_CFLAGS) -I$(PATH_BBBIO)BBBio_lib/ -fPIC -fvisibility=hidden -L$(PATH_BBBIO)
LDFLAGS=$(MODE_LDFLAGS) -L$(PATH_BBBIO) -shared
LIB_STA=-lBBBio
LIB_DYN=-lrt
SRC=dallas.c
OBJ=$(SRC:%.c=%.o)
OLIB=libDallas.so



.PHONY: all clean cleannolib

all: precompile $(OBJ) $(OLIB)

cleannolib:
	rm -f $(OBJ)
	
clean: cleannolib
	rm -f $(OLIB)

precompile: $(PATH_BBBIO)libBBBio.a
$(PATH_BBBIO)libBBBio.a:
	make -C$(PATH_BBBIO)

	
$(OLIB): $(OBJ)
	$(CC) $(LDFLAGS) $(LIB_DYN) $(OBJ) -o $@ $(LIB_STA)
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

