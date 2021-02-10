CFLAGS=-m64 -fPIC -g -I../../heclib/headers -I../../heclib/grid
#CPPFLAGS= -std=c++11 -m64 -fPIC -g -I../../heclib/headers -I../../heclib/grid
CPPFLAGS=  -m64 -fPIC -g -I../../heclib/headers 

CPP_SRCS:=$(wildcard *.cpp)
CPP_OBJS=$(CPP_SRCS:.cpp=.o)

C_SRCS:=$(wildcard *.c)
C_OBJS=$(C_SRCS:.c=.o)
LIBS=../../heclib/Output/heclib.a -lgfortran 

all: grid.a

grid.a: $(CPP_OBJS) $(C_OBJS)
	ar rvs  $@ $(CPP_OBJS) $(C_OBJS) 

.cpp.o:
	$(CXX) $(CPPFLAGS) -c $<

.c.o:
	$(CC) $(CFLAGS) -c $<

.PHONY: clean

clean:
	rm  -f $(CPP_OBJS) $(C_OBJS) grid.a