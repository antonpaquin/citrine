#! powershell

$ScriptDir = Split-Path $script:MyInvocation.MyCommand.Path
cd $ScriptDir\..

cp package\pyinstaller_win10.spec citrine-ui.spec
pyinstaller citrine-ui.spec

rm citrine-ui.spec
mv .\dist\citrine-ui ..\artifacts\citrine-ui-win10
