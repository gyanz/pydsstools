#!/bin/bash
# set -x

# Run the python test
for py in ${@:2}
do
    python "/pydsstools/examples/$py"
done

# Keep container running
while $1
do
    sleep 10000
done
