# FROM ubuntu:20.04
FROM osgeo/gdal

# Environment
# ENV BUILD_DEST=/build
# ENV PY_INCL=/usr/include/python3.8
# ENV DSS7_INCL=/DSS/headers
# ENV DSS7_LIB=/DSS
# ENV EXT_NAME=core_heclib
# ENV EXT_C_FILE=$EXT_NAME.c
# ENV EXT_MODULE=$BUILD_DEST/pydsstools/pydsstools/_lib/x64/py38/$EXT_NAME.so

# Python Dependencies
RUN apt-get -y update \
    && apt-get -y install git wget unzip \
    python3-dev python3-pip gfortran python3-numpy-dev

RUN python3 -m pip install cython

RUN git clone https://github.com/gyanz/pydsstools.git && pip install /pydsstools/dist/pydsstools-2.1-cp38-cp38-linux_x86_64.whl

# HEC-DSS Dependencies
# RUN mkdir -p /DSS \
#     && cd DSS \
#     && wget https://www.hec.usace.army.mil/nexus/repository/heclib/7-HX/DSS_DSS-linux_88_artifacts.zip \
#     && unzip /DSS/DSS_DSS-linux_88_artifacts.zip \
#     && rm ./DSS_DSS-linux_88_artifacts.zip


# Build pydsstools
# RUN mkdir -p /pydsstools /build
# COPY . /pydsstools

# Copy Source to build directory
# Remove pre-built libraries included in repository
# Ensure __init__.py exists
# RUN cp -r /pydsstools $BUILD_DEST/ \
#     && rm -rf $BUILD_DEST/pydsstools/pydsstools/_lib/x64/py38/* \
#     && touch $BUILD_DEST/pydsstools/pydsstools/_lib/x64/py38/__init__.py

# Build
# RUN cd pydsstools/pydsstools/src \
#     && cython -3 ./core_heclib.pyx -o $EXT_C_FILE \
#     && gcc -Wall -Wl,--unresolved-symbols=report-all,--warn-unresolved-symbols,--warn-once \
#     -shared -fPIC $EXT_C_FILE -I"$DSS7_INCL" -I"$PY_INCL" -L"$DSS7_LIB" -l:heclib.a -lgfortran -lm -lquadmath -lz \
#     -o"$EXT_MODULE"

# RUN pip3 install ${BUILD_DEST}/pydsstools

# RUN python3 $BUILD_DEST/pydsstools/pydsstools/examples/example10.py

COPY run.sh example.py example1.py mbrfc-krf-qpe-01h_krfqpe_2021062501z.tif /

# RUN python3 example.py \
#     && python3 example1.py

CMD ["/run.sh"]
