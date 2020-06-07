#! powershell

$ScriptDir = Split-Path $script:MyInvocation.MyCommand.Path
cd $ScriptDir\..

cp package\pyinstaller_win10.spec hivemind-daemon.spec
pyinstaller hivemind-daemon.spec

rm hivemind-daemon.spec
mv .\dist\hivemind-daemon ..\artifacts\hivemind-daemon-win10
