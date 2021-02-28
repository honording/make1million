#!/bin/bash

PWD=$(eval pwd)

WORKDIR="/code"

mkdir -p ./.tokens

docker run \
    -ti \
    --rm \
    --network=host \
    --workdir ${WORKDIR} \
    --env WORKSPACE=${WORKDIR} \
    -v $PWD/src:${WORKDIR}/src:ro \
    -v $PWD/config:${WORKDIR}/config:ro \
    -v $PWD/.tokens:/root/.tokens \
    python3 \
    /bin/bash
    