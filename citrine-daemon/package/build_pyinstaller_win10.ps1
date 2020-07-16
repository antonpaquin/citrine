#! powershell

$ScriptDir = Split-Path $script:MyInvocation.MyCommand.Path
cd $ScriptDir\..

cp package\pyinstaller_win10.spec citrine-daemon.spec
pyinstaller citrine-daemon.spec

rm citrine-daemon.spec
mv .\dist\citrine-daemon ..\artifacts\citrine-daemon-win10
