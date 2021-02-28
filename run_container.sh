#!/bin/bash

PWD=$(eval pwd)

WORKDIR="/code"

mkdir -p ./.tokens
mkdir -p ./.actions

docker run \
    -ti \
    --rm \
    --network=host \
    --workdir ${WORKDIR} \
    --env WORKSPACE=${WORKDIR} \
    -v $PWD/src:${WORKDIR}/src:ro \
    -v $PWD/config:${WORKDIR}/config:ro \
    -v $PWD/.tokens:/root/.tokens \
    -v $PWD/.actions:/root/.actions \
    python3 \
    /bin/bash
    