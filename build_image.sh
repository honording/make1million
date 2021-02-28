#!/bin/bash

docker image build -f ./res/python.dockerfile -t python3 .

docker image prune -f
