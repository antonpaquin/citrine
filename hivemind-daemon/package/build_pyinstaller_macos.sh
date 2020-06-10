#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"
cd ..

set -ex

cp package/pyinstaller_macos.spec hivemind-daemon.spec
pyinstaller hivemind-daemon.spec
rm -r ../artifacts/hivemind-daemon-macos || true
codesign --remove-signature dist/hivemind-daemon/Python
mv dist/hivemind-daemon ../artifacts/hivemind-daemon-macos

rmdir dist
rm -rf build/
rm hivemind-daemon.spec
