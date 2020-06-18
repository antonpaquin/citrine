#! powershell (does windows even care about the shebang?)

Add-Type -AssemblyName System.IO.Compression.FileSystem
function Unzip
{
    param([string]$zipfile, [string]$outpath)

    [System.IO.Compression.ZipFile]::ExtractToDirectory($zipfile, $outpath)
}

rmdir -Recurse .\hivemind -ErrorAction SilentlyContinue
Unzip "C:\Users\build\hivemind_src.zip" "C:\Users\build\hivemind"
rm hivemind_src.zip
mv .\res .\hivemind\res
mv hivemind.wxs .\hivemind\hivemind.wxs
cd hivemind

pip install --upgrade pip
pip install --upgrade virtualenv

python -m virtualenv env
.\env/Scripts/Activate.ps1
pip install --upgrade pip

# Newest versions (as fetched by setup.py) are borked by some dll crap
pip install PySide2==5.14.2.2

pip install .\hivemind-daemon
pip install .\hivemind-client
pip install .\hivemind-ui

pip install pyinstaller

mkdir artifacts

# Apparently working directory is not scoped to the script
$WORKDIR = $pwd
.\hivemind-daemon\package\build_pyinstaller_win10.ps1
cd $WORKDIR
.\hivemind-client\package\build_pyinstaller_win10.ps1
cd $WORKDIR
.\hivemind-ui\package\build_pyinstaller_win10.ps1
cd $WORKDIR

mkdir hivemind-win10
robocopy .\artifacts\hivemind-daemon-win10 .\hivemind-win10 /e /copyall
robocopy .\artifacts\hivemind-client-win10 .\hivemind-win10 /e /copyall
robocopy .\artifacts\hivemind-ui-win10 .\hivemind-win10 /e /copyall
cp .\res\logo_1024.png .\hivemind-win10
cp .\res\logo_256.ico .\hivemind-win10

..\wix\heat.exe dir .\hivemind-win10\ -ag -cg HivemindCG -dr INSTALLDIR -sw 5150 -var 'var.src' -out data.wxs
..\wix\candle.exe .\hivemind.wxs .\data.wxs -dsrc=hivemind-win10
..\wix\light.exe .\hivemind.wixobj .\data.wixobj -o hivemind-win10.msi
mv hivemind-win10.msi artifacts
