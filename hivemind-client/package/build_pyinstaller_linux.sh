#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"
cd ..

set -ex

cp package/pyinstaller_linux.spec hivemind-client.spec
pyinstaller hivemind-client.spec
rm -r ../artifacts/hivemind-client-linux || true
mv dist/hivemind-client ../artifacts/hivemind-client-linux

rmdir dist
rm -rf build/
rm hivemind-client.spec
