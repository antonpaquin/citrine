#! /bin/bash

set -ex

apt update
apt install -y python3.7 python3.7-dev python3.7-venv python3-pip

# for pyside2
apt install -y libgssapi-krb5-2

python3.7 -m venv env
source env/bin/activate

pip install wheel
pip install pyinstaller
pip install -e citrine-daemon
pip install -e citrine-client
pip install -e citrine-ui

pushd citrine-daemon
./package/build_pyinstaller_linux.sh
popd

pushd citrine-client
./package/build_pyinstaller_linux.sh
popd

pushd citrine-ui
./package/build_pyinstaller_linux.sh
popd
