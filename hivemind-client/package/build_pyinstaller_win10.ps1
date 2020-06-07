#! powershell

$ScriptDir = Split-Path $script:MyInvocation.MyCommand.Path
cd $ScriptDir\..

cp package\pyinstaller_win10.spec hivemind-client.spec
pyinstaller hivemind-client.spec

rm hivemind-client.spec
mv .\dist\hivemind-client ..\artifacts\hivemind-client-win10
