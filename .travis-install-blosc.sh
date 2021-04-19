#!/usr/bin/env bash
set -e
BLOSC=c-blosc-1.14.2

# check to see if blosc folder is empty
if [ ! -d "$RUNNER_WORKSPACE/hexitec-detector/${BLOSC}/lib" ]; then
  curl --output ${BLOSC}.tar.gz -L https://codeload.github.com/Blosc/c-blosc/tar.gz/v1.14.2;
  tar -zxf ${BLOSC}.tar.gz;
  cd ${BLOSC};
  mkdir build;
  cd build;
  cmake -DCMAKE_INSTALL_PREFIX=$RUNNER_WORKSPACE/hexitec-detector/$BLOSC ..;
  cmake --build . --target install;
else
  echo 'Using cached directory.';
fi
