#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"
cd ..

set -ex

cp package/pyinstaller_linux.spec hivemind-daemon.spec
pyinstaller hivemind-daemon.spec
mv dist/hivemind-daemon ../artifacts/hivemind-daemon

rmdir dist
rm -rf build/
rm hivemind-daemon.spec
