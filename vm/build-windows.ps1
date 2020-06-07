#! powershell (does windows even care about the shebang?)

Add-Type -AssemblyName System.IO.Compression.FileSystem
function Unzip
{
    param([string]$zipfile, [string]$outpath)

    [System.IO.Compression.ZipFile]::ExtractToDirectory($zipfile, $outpath)
}

rmdir -Recurse .\hivemind -ErrorAction SilentlyContinue
Unzip "C:\Users\build\hivemind_src.zip" "C:\Users\build\hivemind"
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
