#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"
cd ..

set -ex

cp package/pyinstaller_macos.spec citrine-daemon.spec
pyinstaller citrine-daemon.spec
rm -r ../artifacts/citrine-daemon-macos || true
codesign --remove-signature dist/citrine-daemon/Python
mv dist/citrine-daemon ../artifacts/citrine-daemon-macos

rmdir dist
rm -rf build/
rm citrine-daemon.spec
