#!/bin/sh
PYTHON_EXE=`which python`
JCD_HOME=`dirname $0`

exec $PYTHON_EXE $JCD_HOME/src/jcd.py $*