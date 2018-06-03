#!/bin/bash

PATH_BIN_PYTHON="/usr/bin/python"
PATH_BIN_PIP="$(which pip)"

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PATH_APP="$CURRENT_DIR/app"

echo "[CAMERA-TIMELAPSE] Booting."
cd "$PATH_APP"

echo "[CAMERA-TIMELAPSE] Starting service."

$PATH_BIN_PYTHON boot.py
