#!/bin/bash
# Helper script for building core_heclib.so; linux x64 (ubuntu:20.04); python3.8
IMAGE_NAME=pydsstools_linux_x64_py38_builder

# Build Image
docker build -t ${IMAGE_NAME} .

# Run image as container; extract core_heclib.so from container
# and save to host OS in dedicated location in git repository.
# Referenced: https://www.reddit.com/r/docker/comments/9ou9wx/getting_build_artifacts_out_of_docker_image/
#             https://docs.docker.com/engine/reference/commandline/cp/
CID=$(docker create ${IMAGE_NAME})

docker cp ${CID}:build/pydsstools/pydsstools/_lib/x64/py38/core_heclib.so \
          pydsstools/_lib/x64/py38/core_heclib.so
