#! powershell

$ScriptDir = Split-Path $script:MyInvocation.MyCommand.Path
cd $ScriptDir\..

cp package\pyinstaller_win10.spec hivemind-ui.spec
pyinstaller hivemind-ui.spec

rm hivemind-ui.spec
mv .\dist\hivemind-ui ..\artifacts\hivemind-ui-win10
