#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"
cd ..

set -ex

cp package/pyinstaller_linux.spec citrine-daemon.spec
pyinstaller citrine-daemon.spec
rm -r ../artifacts/citrine-daemon-linux || true
mv dist/citrine-daemon ../artifacts/citrine-daemon-linux

rmdir dist
rm -rf build/
rm citrine-daemon.spec
