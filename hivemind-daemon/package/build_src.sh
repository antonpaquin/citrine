#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"
cd ..

set -ex

SRC=$(find . -type f \
	! -path './.idea*' \
	! -path './artifacts*' \
	! -path './build_pkg*' \
	! -path './hivemind_daemon.egg-info*' \
	! -path './onnx*' \
	! -path '*/__pycache__*' \
	! -path './snapcraft.yaml' \
	! -path '*.snap')

zip -r9 hivemind_daemon_src.zip $SRC
mv hivemind_daemon_src.zip artifacts
