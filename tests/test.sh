#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "Script dir: $SCRIPT_DIR"

${SCRIPT_DIR}/../setup.sh -v -n

cd ${SCRIPT_DIR}/..

source ./venv/bin/activate

python -m unittest discover -s tests
