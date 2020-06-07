#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"
cd ..

set -ex

cp package/pyinstaller_linux.spec hivemind-cli.spec
pyinstaller hivemind-cli.spec
mv dist/hivemind-ui ../artifacts/hivemind-ui

rmdir dist
rm -rf build/
rm hivemind-cli.spec
