#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"
cd ..

set -ex

cp package/pyinstaller_linux.spec hivemind-ui.spec
pyinstaller hivemind-ui.spec
rm -r ../artifacts/hivemind-ui-linux || true
mv dist/hivemind-ui ../artifacts/hivemind-ui-linux

rmdir dist
rm -rf build/
rm hivemind-ui.spec
