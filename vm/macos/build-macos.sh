#! /bin/bash

set -ex

rm -rf hivemind || true
unzip hivemind_src.zip -d hivemind
mv QtQmlModels.patch hivemind
mv res hivemind
cd hivemind

PATH="/usr/local/bin:$PATH"

pip3 install --upgrade pip
pip3 install --upgrade virtualenv

python3 -m virtualenv env
source env/bin/activate
pip install --upgrade pip

pip install ./hivemind-daemon
pip install ./hivemind-client
pip install ./hivemind-ui

pip install pyinstaller
patch env/lib/python3.7/site-packages/PyInstaller/hooks/hook-PySide2.QtWebEngineWidgets.py QtQmlModels.patch

mkdir artifacts

# Create runnable binaries

./hivemind-daemon/package/build_pyinstaller_macos.sh
./hivemind-client/package/build_pyinstaller_macos.sh
./hivemind-ui/package/build_pyinstaller_macos.sh

# Merge binaries into a single directory

mkdir artifacts/hivemind-macos
rsync -r artifacts/hivemind-daemon-macos/ artifacts/hivemind-macos/
rsync -r artifacts/hivemind-client-macos/ artifacts/hivemind-macos/
rsync -r artifacts/hivemind-ui-macos/ artifacts/hivemind-macos/

# Create app bundle

mkdir Hivemind.app
mkdir Hivemind.app/Contents
cp -r artifacts/hivemind-macos/* Hivemind.app/Contents/
mkdir Hivemind.app/Contents/Resources
mv ../Info.plist Hivemind.app/Contents/Info.plist
mv Hivemind.app/Contents/hivemind hivemind.app/Contents/hivemind-client
mv Hivemind.app/Contents/hivemind-ui hivemind.app/Contents/Hivemind

mkdir Hivemind.iconset
for f in 512 256 128 64 32 16; do
  f2=$(expr $f \* 2)
  cp res/logo_$f.png Hivemind.iconset/icon_"$f"x"$f".png
  cp res/logo_$f2.png Hivemind.iconset/icon_"$f"x"$f"@2x.png
done
iconutil -c icns Hivemind.iconset
mv Hivemind.icns Hivemind.app/Contents/Resources/Hivemind.icns

# Create DMG installer

SIZE=$(du -sk Hivemind.app | awk '{print $1}')
SIZE=$(expr $SIZE + 10000)
hdiutil create -srcfolder "Hivemind.app" -volname "Hivemind" -fs HFS+ -fsargs "-c c=64,a=16,e=16" -format UDRW -size ${SIZE}k pack.temp.dmg
DEVICE=$(hdiutil attach -readwrite -noverify -noautoopen "pack.temp.dmg" | egrep '^/dev/' | sed 1q | awk '{print $1}')
sleep 3

echo '
   tell application "Finder"
     tell disk "Hivemind"
           open
           set current view of container window to icon view
           set toolbar visible of container window to false
           set statusbar visible of container window to false
           set the bounds of container window to {400, 100, 885, 430}
           set theViewOptions to the icon view options of container window
           set arrangement of theViewOptions to not arranged
           set icon size of theViewOptions to 72
           make new alias file at container window to POSIX file "/Applications" with properties {name:"Applications"}
           set position of item "Hivemind" of container window to {100, 100}
           set position of item "Applications" of container window to {375, 100}
           update without registering applications
           delay 5
           close
     end tell
   end tell
' | osascript && echo "THIS IS WAITING ON THE GUI"

chmod -Rf go-w /Volumes/Hivemind
sync
sync
hdiutil detach ${DEVICE}
hdiutil convert "pack.temp.dmg" -format UDZO -imagekey zlib-level=9 -o "Hivemind.dmg"
rm -f pack.temp.dmg

mv Hivemind.dmg artifacts
