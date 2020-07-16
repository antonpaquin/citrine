#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"
cd ..

set -ex

cp package/pyinstaller_linux.spec citrine-ui.spec
pyinstaller citrine-ui.spec
rm -r ../artifacts/citrine-ui-linux || true
mv dist/citrine-ui ../artifacts/citrine-ui-linux

rmdir dist
rm -rf build/
rm citrine-ui.spec
