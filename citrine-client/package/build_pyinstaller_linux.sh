#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"
cd ..

set -ex

cp package/pyinstaller_linux.spec citrine-client.spec
pyinstaller citrine-client.spec
rm -r ../artifacts/citrine-client-linux || true
mv dist/citrine-client ../artifacts/citrine-client-linux

rmdir dist
rm -rf build/
rm citrine-client.spec
