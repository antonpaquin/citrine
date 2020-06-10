#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"
cd ..

set -ex

cp package/pyinstaller_macos.spec hivemind-ui.spec
pyinstaller hivemind-ui.spec
rm -r ../artifacts/hivemind-ui-macos || true
codesign --remove-signature dist/hivemind-ui/Python
mv dist/hivemind-ui ../artifacts/hivemind-ui-macos

rmdir dist
rm -rf build/
rm hivemind-ui.spec
