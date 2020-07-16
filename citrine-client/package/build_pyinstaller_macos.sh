#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"
cd ..

set -ex

cp package/pyinstaller_macos.spec citrine-client.spec
pyinstaller citrine-client.spec
rm -r ../artifacts/citrine-client-macos || true
codesign --remove-signature dist/citrine-client/Python
mv dist/citrine-client ../artifacts/citrine-client-macos

rmdir dist
rm -rf build/
rm citrine-client.spec
