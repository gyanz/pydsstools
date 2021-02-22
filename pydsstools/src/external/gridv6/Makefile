CFLAGS=-m64 -v -fPIC -g -I../dss/headers -Iheaders
CPPFLAGS=-m64 -v -fPIC -g -I../dss/headers -Iheaders

CPP_SRCS:=$(wildcard *.cpp)
CPP_OBJS=$(CPP_SRCS:.cpp=.o)

C_SRCS:=$(wildcard *.c)
C_OBJS=$(C_SRCS:.c=.o)

OUTDIR=build 

all: grid.a

grid.a: $(CPP_OBJS) $(C_OBJS)
	ar rvs  $@ $(CPP_OBJS) $(C_OBJS)
	mv -f grid.a $(OUTDIR) 

.cpp.o:
	$(CXX) $(CPPFLAGS) -c $<

.c.o:
	$(CC) $(CFLAGS) -c $<

.PHONY: clean

clean:
	rm  -f $(CPP_OBJS) $(C_OBJS) $(OUTDIR)/grid.a
