#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"
cd ..

set -ex

cp package/pyinstaller_macos.spec citrine-ui.spec
pyinstaller citrine-ui.spec
rm -r ../artifacts/citrine-ui-macos || true
codesign --remove-signature dist/citrine-ui/Python
mv dist/citrine-ui ../artifacts/citrine-ui-macos

rmdir dist
rm -rf build/
rm citrine-ui.spec
