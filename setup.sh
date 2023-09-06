#!/bin/bash
# Copyright (c) 2018-2023, The Storage Networking Industry Association.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# Neither the name of The Storage Networking Industry Association (SNIA) nor
# the names of its contributors may be used to endorse or promote products
# derived from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#  THE POSSIBILITY OF SUCH DAMAGE.

BASE_DIR=$(pwd)

API_PORT=5001
SETUP_ONLY=
VIRTUAL_ENV=

COMMON_NAME="$1"
EXTFILE=certificate_config.cnf

function print_help {
    cat <<EOF

Helper to set up a Swordfish emulator. This will take care of getting the
necessary source files ready and start a local instance of the emulator.

USAGE:

    $(basename $0) [--port PORT] [--no-start] [--virtual-env]

Options:

    -p | --port PORT     -- Port to run the emulator on. Default is $API_PORT.

    -n | --no-start      -- Prepare the emulator but do not start it.

    -v | --virtual-env   -- Create a virtual environment with all needed in './venv'

EOF
}

# Extract command line args
while [ "$1" != "" ]; do
    case $1 in
        -p | --port )
            shift
            API_PORT=$1
            ;;
        -n | --no-start)
            SETUP_ONLY="true"
            ;;
        -v | --virtual-env)
            VIRTUAL_ENV="true"
            ;;
        *)
            print_help
            exit 1
    esac
    shift
done

# Do some system sanity checks first
if ! [ -x "$(command -v python3)" ] ; then
    echo "Error: python3 is required to run the emulator and executable not" \
         "found"
    echo ""
    echo "See https://www.python.org/downloads/ for installation instructions."
    echo ""
    exit 1
fi

if ! [ -x "$(command -v virtualenv)" ]; then
    echo "Error: virtualenv is required."
    echo ""
    echo "See https://virtualenv.pypa.io/en/stable/installation/ for" \
         "installation instructions."
    echo ""
    exit 1
fi

if ! [ -x "$(command -v git)" ]; then
    echo "Error: git is required."
    echo ""
    echo "See https://git-scm.com/book/en/v2/Getting-Started-Installing-Git" \
         "for installation instructions."
    echo ""
    exit 1
fi

# Set up our virtual environment
if [ "$VIRTUAL_ENV" == "true" ]; then
    echo "Setting up emulator Python virtualenv and requirements..."
    virtualenv --python=python3 venv
    venv/bin/pip install -q -r requirements.txt
fi

# generating server key
echo "Generating private key"
openssl genrsa -out "$BASE_DIR"/server.key 2048

# generating public key
echo "Generating public key"
openssl rsa -in "$BASE_DIR"/server.key -pubout -out "$BASE_DIR"/server_public.key

# ## Update Common Name in External File
# /bin/echo "commonName              = $COMMON_NAME" >> $EXTFILE

# Generating Certificate Signing Request using config file
echo "Generating Certificate Signing Request"
openssl req -new -key "$BASE_DIR"/server.key -out "$BASE_DIR"/server.csr -config "$BASE_DIR"/$EXTFILE

echo "Generating self signed certificate"
openssl x509 -in "$BASE_DIR"/server.csr -out "$BASE_DIR"/server.crt -req -signkey "$BASE_DIR"/server.key -days 365 -extfile "$BASE_DIR"/v3.ext

if [ "$SETUP_ONLY" == "true" ]; then
    echo ""
    echo "Emulator files have been prepared. Run the following to start the" \
         "emulator:"
    echo ""
    echo "   python3 ofmf-main.py"
    echo " or if you have set up a virtual environment: (see -v option)"
    echo "   venv/bin/python ofmf-main.py"
    echo ""
    exit 0
fi

# Start up the emulator
cat <<EOF

---------------------------------------------------------------------
Starting Swordfish emulator. Access the local instance using the URL:

   http://localhost:$API_PORT

$(tput bold)Press Ctrl-C when done.$(tput sgr0)
---------------------------------------------------------------------
EOF

echo ""
if [ -d "venv" ]; then
    venv/bin/python ofmf-main.py -port $API_PORT
    echo ""
    echo ""
    echo "Emulator can be rerun from here by running the command:"
    echo "   venv/bin/python ofmf-main.py"
else
    #python3 ofmf-main.py -port $API_PORT
    res=$(python3 ofmf-main.py -port $API_PORT)
    echo $res
    echo ""
    echo ""
    echo "Emulator can be rerun from here by running the command:"
    echo "   python3 ofmf-main.py"
    echo ""
    echo "If running './setup.sh' complains about a missing module,"
    echo "  try considering './setup.sh -v' to create a virtual environment"
fi
echo ""
