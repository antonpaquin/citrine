#! powershell

$ScriptDir = Split-Path $script:MyInvocation.MyCommand.Path
cd $ScriptDir\..

cp package\pyinstaller_win10.spec citrine-client.spec
pyinstaller citrine-client.spec

rm citrine-client.spec
mv .\dist\citrine-client ..\artifacts\citrine-client-win10
